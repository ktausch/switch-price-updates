resource "aws_iam_role" "execution_role" {
  name = "${var.function_name}_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

data "archive_file" "code_zip" {
  type        = "zip"
  output_path = "${var.function_name}____code.zip"
  dynamic "source" {
    for_each = var.file_manifest
    content {
      filename = source.value
      content  = file("${var.code_directory}/${source.value}")
    }
  }
}

resource "aws_lambda_function" "function" {
  filename         = data.archive_file.code_zip.output_path
  source_code_hash = data.archive_file.code_zip.output_base64sha256
  function_name    = var.function_name
  role             = aws_iam_role.execution_role.arn
  handler          = var.handler
  runtime          = var.runtime
  timeout          = var.timeout
  environment {
    variables = var.environment_variables
  }
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${aws_lambda_function.function.function_name}"
  retention_in_days = 14
}

resource "aws_iam_policy" "logging_policy" {
  description = "Allows the store checker subscribe lambda to add logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.log_group.arn}:*"
        Effect   = "Allow"
        Sid      = ""
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "logging_policy_attachment" {
  role       = aws_iam_role.execution_role.name
  policy_arn = aws_iam_policy.logging_policy.arn
}

resource "null_resource" "delete_zip" {
  depends_on = [aws_lambda_function.function]
  triggers = {
    zip_file   = data.archive_file.code_zip.output_path
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "rm ${data.archive_file.code_zip.output_path}"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "touch ${self.triggers.zip_file} ; rm ${self.triggers.zip_file}"
  }
}
