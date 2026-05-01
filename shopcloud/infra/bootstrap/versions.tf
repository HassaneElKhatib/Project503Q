terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.50, < 7.0"
    }
  }
  # Bootstrap is intentionally local-state. After it's applied, every
  # other env uses the bucket + DynamoDB table it produces.
}
