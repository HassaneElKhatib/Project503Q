resource "aws_kms_key" "eks_secrets" {
  count = var.enable_kms_secrets_encryption ? 1 : 0

  description             = "KMS envelope encryption for Kubernetes secrets (${var.cluster_name})"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableAccountRootPermissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowEksServiceUse"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:CreateGrant"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-eks-secrets"
  })
}

resource "aws_kms_alias" "eks_secrets" {
  count = var.enable_kms_secrets_encryption ? 1 : 0

  name          = "alias/${var.cluster_name}-eks-secrets"
  target_key_id = aws_kms_key.eks_secrets[0].key_id
}
