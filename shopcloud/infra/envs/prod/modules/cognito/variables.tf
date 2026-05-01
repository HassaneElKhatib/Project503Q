variable "environment" {
  description = "Environment name, for example dev or prod."
  type        = string
}

variable "region" {
  description = "AWS region."
  type        = string
}

variable "customer_domain_prefix" {
  description = "Unique Cognito hosted UI domain prefix for customer auth."
  type        = string
}

variable "admin_domain_prefix" {
  description = "Unique Cognito hosted UI domain prefix for admin auth."
  type        = string
}

variable "customer_callback_url" {
  description = "Customer auth callback URL."
  type        = string
}

variable "customer_logout_url" {
  description = "Customer logout redirect URL."
  type        = string
}

variable "admin_callback_url" {
  description = "Admin auth callback URL."
  type        = string
}

variable "admin_logout_url" {
  description = "Admin logout redirect URL."
  type        = string
}

variable "cookie_domain" {
  description = "Cookie domain used by the auth service."
  type        = string
}

variable "kms_key_id" {
  description = "Optional KMS key ID or ARN for Secrets Manager encryption."
  type        = string
  default     = null
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}