output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  value     = aws_eks_cluster.this.certificate_authority[0].data
  sensitive = true
}

output "node_security_group_id" {
  value = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}

output "catalog_irsa_role_arn" {
  value = try(aws_iam_role.irsa["catalog"].arn, null)
}

output "auth_irsa_role_arn" {
  value = try(aws_iam_role.irsa["auth"].arn, null)
}

output "cart_irsa_role_arn" {
  value = try(aws_iam_role.irsa["cart"].arn, null)
}

output "admin_irsa_role_arn" {
  value = try(aws_iam_role.irsa["admin"].arn, null)
}

output "checkout_irsa_role_arn" {
  value = try(aws_iam_role.irsa["checkout"].arn, null)
}

output "db_migrate_irsa_role_arn" {
  value = try(aws_iam_role.irsa["db_migrate"].arn, null)
}

output "vpc_id" {
  description = "VPC ID inferred from the first private subnet."
  value       = data.aws_subnet.first_private.vpc_id
}

output "kms_secrets_key_arn" {
  description = "KMS CMK ARN for Kubernetes Secrets envelope encryption (null if disabled)."
  value       = try(aws_kms_key.eks_secrets[0].arn, null)
}

output "aws_load_balancer_controller_irsa_role_arn" {
  value = try(aws_iam_role.aws_load_balancer_controller[0].arn, null)
}

output "cluster_autoscaler_irsa_role_arn" {
  value = try(aws_iam_role.cluster_autoscaler[0].arn, null)
}

output "external_secrets_irsa_role_arn" {
  value = try(aws_iam_role.external_secrets[0].arn, null)
}
