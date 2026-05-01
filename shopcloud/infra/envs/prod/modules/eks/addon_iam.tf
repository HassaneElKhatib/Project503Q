# IAM roles for cluster add-on Helm charts (ALB Controller, Cluster Autoscaler, External Secrets).
# Created when enable_helm_addons = true; paired with modules/eks_helm_addons.

locals {
  alb_controller_sa_sub            = "system:serviceaccount:kube-system:aws-load-balancer-controller"
  cluster_autoscaler_sa_sub        = "system:serviceaccount:kube-system:cluster-autoscaler"
  external_secrets_operator_sa_sub = "system:serviceaccount:external-secrets-system:external-secrets"

  external_secrets_kms_decrypt_arns = distinct(concat(
    var.external_secrets_kms_key_arns,
    var.enable_kms_secrets_encryption && var.enable_helm_addons ? [aws_kms_key.eks_secrets[0].arn] : [],
  ))
}

data "aws_iam_policy_document" "alb_controller_assume" {
  count = var.enable_helm_addons ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:sub"
      values   = [local.alb_controller_sa_sub]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "aws_load_balancer_controller" {
  count = var.enable_helm_addons ? 1 : 0

  name               = "${var.cluster_name}-aws-lb-controller"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume[0].json

  tags = merge(var.tags, { Purpose = "aws-load-balancer-controller" })
}

resource "aws_iam_role_policy" "aws_load_balancer_controller" {
  count = var.enable_helm_addons ? 1 : 0

  name = "${var.cluster_name}-alb-ctrl-inline"
  role = aws_iam_role.aws_load_balancer_controller[0].id

  policy = file("${path.module}/policies/alb_controller_iam_policy.json")
}

data "aws_iam_policy_document" "cluster_autoscaler_assume" {
  count = var.enable_helm_addons ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:sub"
      values   = [local.cluster_autoscaler_sa_sub]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "cluster_autoscaler" {
  count = var.enable_helm_addons ? 1 : 0

  statement {
    sid    = "AutoscalingRead"
    effect = "Allow"
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeScalingActivities",
      "autoscaling:DescribeTags",
      "ec2:DescribeImages",
      "ec2:DescribeInstances",
      "ec2:DescribeLaunchTemplateVersions",
      "ec2:DescribeLaunchTemplates",
      "ec2:GetInstanceTypesFromInstanceRequirements",
      "eks:DescribeNodegroup",
      "ec2:DescribeInstanceTypes",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AutoscalingWrite"
    effect = "Allow"
    actions = [
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "autoscaling:UpdateAutoScalingGroup",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "cluster_autoscaler" {
  count = var.enable_helm_addons ? 1 : 0

  name               = "${var.cluster_name}-cluster-autoscaler"
  assume_role_policy = data.aws_iam_policy_document.cluster_autoscaler_assume[0].json

  tags = merge(var.tags, { Purpose = "cluster-autoscaler" })
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  count = var.enable_helm_addons ? 1 : 0

  name   = "${var.cluster_name}-cluster-autoscaler-inline"
  role   = aws_iam_role.cluster_autoscaler[0].id
  policy = data.aws_iam_policy_document.cluster_autoscaler[0].json
}

data "aws_iam_policy_document" "external_secrets_assume" {
  count = var.enable_helm_addons ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:sub"
      values   = [local.external_secrets_operator_sa_sub]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "external_secrets" {
  count = var.enable_helm_addons ? 1 : 0

  name               = "${var.cluster_name}-external-secrets"
  assume_role_policy = data.aws_iam_policy_document.external_secrets_assume[0].json

  tags = merge(var.tags, { Purpose = "external-secrets-operator" })
}

data "aws_iam_policy_document" "external_secrets" {
  count = var.enable_helm_addons ? 1 : 0

  statement {
    sid    = "SecretsManagerRead"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:ListSecrets",
    ]
    resources = length(var.external_secrets_allowed_secret_arns) > 0 ? var.external_secrets_allowed_secret_arns : ["*"]
  }

  dynamic "statement" {
    for_each = length(local.external_secrets_kms_decrypt_arns) > 0 ? [1] : []
    content {
      sid    = "KmsDecrypt"
      effect = "Allow"
      actions = [
        "kms:Decrypt",
        "kms:DescribeKey",
      ]
      resources = local.external_secrets_kms_decrypt_arns
    }
  }
}

resource "aws_iam_role_policy" "external_secrets" {
  count = var.enable_helm_addons ? 1 : 0

  name   = "${var.cluster_name}-external-secrets-inline"
  role   = aws_iam_role.external_secrets[0].id
  policy = data.aws_iam_policy_document.external_secrets[0].json
}
