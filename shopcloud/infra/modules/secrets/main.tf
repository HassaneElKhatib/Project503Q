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
