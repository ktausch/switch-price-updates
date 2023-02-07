locals {
  lambda_runtime = "python3.9"
  code_directory = "./lambda_functions"
  lambda_variables = {
    SENDER_INFO          = jsondecode(file("../../email_creds.json"))
    US_ALGOLIA_ID        = "U3B6GR4UA3"
    US_ALGOLIA_KEY       = "c4da8be7fd29f0f5bfa42920b0a99dc7"
    US_GAMES_INDEX_NAME  = "ncom_game_en_us_title_asc"
    SUBSCRIBE_URL_S3_KEY = "url_of_subscription_lambda.txt"
  }
}

resource "aws_s3_bucket" "storechecker" {}

resource "aws_s3_object" "subscribers" {
  bucket  = aws_s3_bucket.storechecker.bucket
  key     = "subscribers.json"
  content = jsonencode({})
}

resource "aws_s3_object" "state" {
  bucket  = aws_s3_bucket.storechecker.bucket
  key     = "state.json"
  content = jsonencode({})
}

module "store_checker_subscribe" {
  source         = "../LambdaWithLogging"
  function_name  = "store_checker_subscription"
  code_directory = local.code_directory
  file_manifest = [
    "game_shop_state.py",
    "get_logger.py",
    "link_formatter.py",
    "send_email.py",
    "subscriber_job.py",
    "subscriber_state.py",
    "subscribe_lambda_function.py",
  ]
  runtime = local.lambda_runtime
  handler = "subscribe_lambda_function.lambda_handler"
  timeout = 10
  environment_variables = {
    SENDER_ADDRESS         = local.lambda_variables.SENDER_INFO.SENDER_ADDRESS
    SENDER_PASSWORD        = local.lambda_variables.SENDER_INFO.SENDER_PASSWORD
    US_ALGOLIA_ID          = local.lambda_variables.US_ALGOLIA_ID
    US_ALGOLIA_KEY         = local.lambda_variables.US_ALGOLIA_KEY
    US_GAMES_INDEX_NAME    = local.lambda_variables.US_GAMES_INDEX_NAME
    STORECHECKER_S3_BUCKET = aws_s3_bucket.storechecker.bucket
    SUBSCRIBERS_S3_KEY     = aws_s3_object.subscribers.key
    SUBSCRIBE_URL_S3_KEY   = local.lambda_variables.SUBSCRIBE_URL_S3_KEY
  }
}

resource "aws_lambda_function_url" "subscribe_url" {
  function_name      = module.store_checker_subscribe.function.function_name
  authorization_type = "NONE"
  cors {
    allow_methods  = ["GET"]
    allow_origins  = ["*"]
    allow_headers  = ["date", "keep-alive"]
    expose_headers = ["keep-alive", "date"]
  }
}

resource "aws_s3_object" "subscribe_url" {
  bucket  = aws_s3_bucket.storechecker.bucket
  key     = local.lambda_variables.SUBSCRIBE_URL_S3_KEY
  content = aws_lambda_function_url.subscribe_url.function_url
}

resource "aws_iam_policy" "store_checker_subscribe_s3" {
  description = "Allows the store checker subscribe lambda to read and write the subscribers (and read its own URL!)"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.storechecker.arn}/${aws_s3_object.subscribers.key}"
        Effect   = "Allow"
        Sid      = "ReadWriteState"
      },
      {
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.storechecker.arn}/${aws_s3_object.subscribe_url.key}"
        Effect   = "Allow"
        Sid      = "ReadUrl"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "store_checker_subscribe_s3_attachment" {
  role       = module.store_checker_subscribe.execution_role.name
  policy_arn = aws_iam_policy.store_checker_subscribe_s3.arn
}

module "store_checker_fulfill" {
  source         = "../LambdaWithLogging"
  function_name  = "store_checker_fulfillment"
  code_directory = local.code_directory
  file_manifest = [
    "game_shop_state.py",
    "get_logger.py",
    "link_formatter.py",
    "send_email.py",
    "subscriber_state.py",
    "update_job.py",
    "update_lambda_function.py",
    "update_state.py"
  ]
  runtime = local.lambda_runtime
  handler = "update_lambda_function.lambda_handler"
  timeout = 10
  environment_variables = {
    SENDER_ADDRESS         = local.lambda_variables.SENDER_INFO.SENDER_ADDRESS
    SENDER_PASSWORD        = local.lambda_variables.SENDER_INFO.SENDER_PASSWORD
    US_ALGOLIA_ID          = local.lambda_variables.US_ALGOLIA_ID
    US_ALGOLIA_KEY         = local.lambda_variables.US_ALGOLIA_KEY
    US_GAMES_INDEX_NAME    = local.lambda_variables.US_GAMES_INDEX_NAME
    STORECHECKER_S3_BUCKET = aws_s3_bucket.storechecker.bucket
    STATE_S3_KEY           = aws_s3_object.state.key
    SUBSCRIBERS_S3_KEY     = aws_s3_object.subscribers.key
    SUBSCRIBE_LAMBDA_URL   = aws_lambda_function_url.subscribe_url.function_url
  }
}

resource "aws_iam_policy" "store_checker_fulfillment_s3" {
  description = "Allows the store checker fulfillment lambda to read and write to the state and read the subscribers"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.storechecker.arn}/${aws_s3_object.state.key}"
        Effect   = "Allow"
        Sid      = "ReadWriteState"
      },
      {
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.storechecker.arn}/${aws_s3_object.subscribers.key}"
        Effect   = "Allow"
        Sid      = "ReadSubscribers"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "store_checker_fulfillment_s3_attachment" {
  role       = module.store_checker_fulfill.execution_role.name
  policy_arn = aws_iam_policy.store_checker_fulfillment_s3.arn
}

resource "aws_cloudwatch_event_rule" "twice_a_day" {
  name                = "TwiceADay"
  description         = "Fires at midnight and 6 PM UTC (11 AM and 5 PM MT) every day."
  schedule_expression = "cron(0 0,18 * * ? *)"
}

resource "aws_cloudwatch_event_target" "run_storechecker_twice_a_day" {
  rule      = aws_cloudwatch_event_rule.twice_a_day.name
  target_id = "lambda"
  arn       = module.store_checker_fulfill.function.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_storechecker" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.store_checker_fulfill.function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.twice_a_day.arn
}
