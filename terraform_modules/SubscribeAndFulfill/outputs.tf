output "subscribe_lambda" {
  value = module.store_checker_subscribe.function
}

output "subscribe_lambda_url" {
  value = aws_lambda_function_url.subscribe_url.function_url
}
