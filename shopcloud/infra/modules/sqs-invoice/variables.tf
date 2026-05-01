variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
}

variable "env" {
  description = "Deployment environment (dev/prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for S3 SSE-KMS and optional Lambda usage."
  type        = string
}

variable "ses_from_address" {
  description = "SES verified sender address for invoice emails."
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to invoice-worker lambda zip artifact."
  type        = string
}

variable "lambda_reserved_concurrent_executions" {
  description = "Cap Lambda concurrency; set only if the account has enough unreserved quota. New/sandbox accounts often cannot reserve (default: use shared pool)."
  type        = number
  default     = null
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
