locals {
  name_prefix = "${var.project_name}-${var.env}"
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.env
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

# This module stays intentionally minimal because the producer modules
# (rds, redis, sqs-invoice) already create the required secrets.
#
# It provides a stable index secret so downstream modules/pipelines can
# discover all shared secret ARNs from one path.
resource "aws_secretsmanager_secret" "index" {
  name                    = "/${var.project_name}/${var.env}/shared/index"
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = var.env == "prod" ? 30 : 7
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}-shared-secrets-index" })
}

resource "aws_secretsmanager_secret_version" "index" {
  secret_id = aws_secretsmanager_secret.index.id
  secret_string = jsonencode({
    database_secret_arn      = var.database_secret_arn
    redis_secret_arn         = var.redis_secret_arn
    invoice_queue_secret_arn = var.invoice_queue_secret_arn
  })
}

resource "random_password" "api_gateway_jwt" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "api_gateway_jwt" {
  name                    = "/${var.project_name}/${var.env}/api-gateway/jwt"
  recovery_window_in_days = var.env == "prod" ? 30 : 7
  kms_key_id              = var.kms_key_arn
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}-api-gateway-jwt" })
}

resource "aws_secretsmanager_secret_version" "api_gateway_jwt" {
  secret_id = aws_secretsmanager_secret.api_gateway_jwt.id
  secret_string = jsonencode({
    secret = random_password.api_gateway_jwt.result
  })
}

# SES SMTP credentials must be created in the SES console (SMTP user); paste into this secret and set
# smtp_enabled=true. Terraform keeps initial placeholders; ignore_changes avoids overwriting manual updates.
resource "aws_secretsmanager_secret" "api_gateway_smtp" {
  name                    = "/${var.project_name}/${var.env}/api-gateway/smtp"
  recovery_window_in_days = var.env == "prod" ? 30 : 7
  kms_key_id              = var.kms_key_arn
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}-api-gateway-smtp" })
}

resource "aws_secretsmanager_secret_version" "api_gateway_smtp" {
  secret_id = aws_secretsmanager_secret.api_gateway_smtp.id
  secret_string = jsonencode({
    smtp_enabled    = "false"
    smtp_host       = "email-smtp.${var.aws_region}.amazonaws.com"
    smtp_port       = "587"
    smtp_user       = "REPLACE_WITH_SES_SMTP_USERNAME"
    smtp_password   = "REPLACE_WITH_SES_SMTP_PASSWORD"
    smtp_from_email = var.smtp_from_address
    smtp_from_name  = "ShopCloud"
    smtp_use_tls    = "true"
    smtp_use_ssl    = "false"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
