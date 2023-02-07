variable "function_name" {
  type        = string
  description = "The name of the function to create"
}

variable "code_directory" {
  type        = string
  description = "The directory where the code exists"
}

variable "file_manifest" {
  type        = list(string)
  description = "List of files to include in the lambda function"
}

variable "runtime" {
  type        = string
  description = "The environment in which to run the lambda function (e.g. python3.9)"
}

variable "handler" {
  type        = string
  description = "The function to call upon entry"
}

variable "timeout" {
  type        = number
  description = "The timeout of the function (in seconds)"
}

variable "environment_variables" {
  type        = map(string)
  description = "The variables that should be accessible in the function"
}
