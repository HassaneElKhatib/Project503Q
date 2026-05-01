locals {
  is_prod = var.env == "prod"

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

data "aws_caller_identity" "current" {}

resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name_prefix}-invoice-dlq"
  message_retention_seconds = 1209600
  kms_master_key_id         = var.kms_key_arn

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-invoice-dlq" })
}

resource "aws_sqs_queue" "main" {
  name                       = "${local.name_prefix}-invoice"
  visibility_timeout_seconds = 14400
  message_retention_seconds  = 345600
  kms_master_key_id          = var.kms_key_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-invoice" })
}

resource "aws_s3_bucket" "invoices" {
  bucket = "${local.name_prefix}-invoices-${data.aws_caller_identity.current.account_id}"
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-invoices" })
}

resource "aws_s3_bucket_public_access_block" "invoices" {
  bucket                  = aws_s3_bucket.invoices.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "invoices" {
  bucket = aws_s3_bucket.invoices.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "invoices" {
  bucket = aws_s3_bucket.invoices.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "invoices" {
  bucket = aws_s3_bucket.invoices.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "invoices" {
  bucket = aws_s3_bucket.invoices.id

  rule {
    id     = "move-invoices-to-glacier"
    status = "Enabled"

    filter {
      prefix = "invoices/"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_ses_email_identity" "from_address" {
  email = var.ses_from_address
}

resource "aws_iam_role" "lambda_exec" {
  name = "${local.name_prefix}-invoice-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_exec" {
  name = "${local.name_prefix}-invoice-worker-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.name_prefix}-invoice-worker:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.main.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.invoices.arn}/invoices/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ses:SendRawEmail"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn
      }
    ]
  })
}

# Omit CMK: shared infra keys often lack logs.eu-central-1.amazonaws.com in policy;
# CloudWatch encrypts log groups with an AWS-managed key by default.
resource "aws_cloudwatch_log_group" "invoice_worker" {
  name              = "/aws/lambda/${local.name_prefix}-invoice-worker"
  retention_in_days = local.is_prod ? 30 : 7

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-invoice-worker-logs" })
}

resource "aws_lambda_function" "invoice_worker" {
  function_name = "${local.name_prefix}-invoice-worker"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"
  filename      = var.lambda_zip_path

  source_code_hash = filebase64sha256(var.lambda_zip_path)
  timeout          = 120
  memory_size      = 512

  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions

  environment {
    variables = {
      INVOICES_BUCKET  = aws_s3_bucket.invoices.bucket
      SES_FROM_ADDRESS = var.ses_from_address
      KMS_KEY_ARN      = var.kms_key_arn
      LOG_LEVEL        = local.is_prod ? "INFO" : "DEBUG"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.invoice_worker,
    aws_iam_role_policy.lambda_exec,
  ]

  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn        = aws_sqs_queue.main.arn
  function_name           = aws_lambda_function.invoice_worker.arn
  batch_size              = 10
  enabled                 = true
  function_response_types = ["ReportBatchItemFailures"]
}

resource "aws_secretsmanager_secret" "invoice_queue" {
  name                    = "/${var.project_name}/${var.env}/sqs/invoice"
  recovery_window_in_days = local.is_prod ? 30 : 7
  kms_key_id              = var.kms_key_arn
  tags                    = merge(local.common_tags, { Name = "${local.name_prefix}-invoice-queue-secret" })
}

resource "aws_secretsmanager_secret_version" "invoice_queue" {
  secret_id = aws_secretsmanager_secret.invoice_queue.id
  secret_string = jsonencode({
    queue_url = aws_sqs_queue.main.url
  })
}
