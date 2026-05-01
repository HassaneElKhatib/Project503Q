variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
}

variable "env" {
  description = "Deployment environment (dev/prod)."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Redis security group."
  type        = string
}

variable "private_data_subnet_ids" {
  description = "Private data subnet IDs for ElastiCache."
  type        = list(string)
}

variable "kms_key_arn" {
  description = "KMS key ARN used for encryption at rest."
  type        = string
}

variable "allowed_security_group_ids" {
  description = "Security groups allowed to access Redis."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
