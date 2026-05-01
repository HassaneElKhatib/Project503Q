locals {
  oidc_provider_url = replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")

  service_account_subjects = {
    catalog    = "system:serviceaccount:${var.service_account_namespace}:catalog"
    auth       = "system:serviceaccount:${var.service_account_namespace}:auth"
    cart       = "system:serviceaccount:${var.service_account_namespace}:cart"
    admin      = "system:serviceaccount:${var.service_account_namespace}:admin"
    checkout   = "system:serviceaccount:${var.service_account_namespace}:checkout"
    db_migrate = "system:serviceaccount:${var.service_account_namespace}:db-migrate"
  }
}

data "aws_iam_policy_document" "irsa_assume_role" {
  for_each = var.enable_irsa ? local.service_account_subjects : {}

  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:sub"
      values   = [each.value]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "irsa" {
  for_each = var.enable_irsa ? local.service_account_subjects : {}

  name = "${var.cluster_name}-${each.key}-irsa"

  assume_role_policy = data.aws_iam_policy_document.irsa_assume_role[each.key].json

  tags = merge(var.tags, {
    Service = each.key
    Purpose = "IRSA"
  })
}

resource "aws_iam_role_policy" "catalog" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-catalog-irsa-policy"
  role = aws_iam_role.irsa["catalog"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_shared_database,
          var.secret_arn_shared_redis
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "auth" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-auth-irsa-policy"
  role = aws_iam_role.irsa["auth"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_cognito_customer
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "cart" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-cart-irsa-policy"
  role = aws_iam_role.irsa["cart"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_shared_redis,
          var.secret_arn_cognito_customer
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "admin" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-admin-irsa-policy"
  role = aws_iam_role.irsa["admin"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_shared_database,
          var.secret_arn_cognito_admin
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "checkout" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-checkout-irsa-policy"
  role = aws_iam_role.irsa["checkout"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_shared_database,
          var.secret_arn_shared_redis,
          var.secret_arn_cognito_customer,
          var.secret_arn_invoice_queue
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = var.invoice_queue_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "db_migrate" {
  count = var.enable_irsa ? 1 : 0

  name = "${var.cluster_name}-db-migrate-irsa-policy"
  role = aws_iam_role.irsa["db_migrate"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.secret_arn_shared_database
        ]
      }
    ]
  })
}