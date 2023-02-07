locals {
  region = "us-west-2"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.1"
    }
  }
}

provider "aws" {
  region = local.region
}

module "subscribe_and_fulfill" {
  source = "./terraform_modules/SubscribeAndFulfill"
}

output "subscribe_lambda_url" {
  value = module.subscribe_and_fulfill.subscribe_lambda_url
}
