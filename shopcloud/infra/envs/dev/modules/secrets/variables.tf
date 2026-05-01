variable "project_name" {
  description = "Project name used in secret paths."
  type        = string
}

variable "env" {
  description = "Deployment environment (dev/prod)."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for secret encryption."
  type        = string
}

variable "aws_region" {
  description = "Regional SES SMTP endpoint (email-smtp.<region>.amazonaws.com)."
  type        = string
}

variable "smtp_from_address" {
  description = "Verified SES sender for api-gateway transactional mail (matches From)."
  type        = string
}

variable "database_secret_arn" {
  description = "Database secret ARN from rds module."
  type        = string
}

variable "redis_secret_arn" {
  description = "Redis secret ARN from redis module."
  type        = string
}

variable "invoice_queue_secret_arn" {
  description = "Invoice queue secret ARN from sqs-invoice module."
  type        = string
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
