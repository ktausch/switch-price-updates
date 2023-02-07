output "execution_role" {
  value = aws_iam_role.execution_role
}

output "function" {
  value = aws_lambda_function.function
}

output "logging_policy_attachment" {
  value = aws_iam_role_policy_attachment.logging_policy_attachment
}
