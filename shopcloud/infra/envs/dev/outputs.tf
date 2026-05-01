############################################
# Identity
############################################
output "environment" {
  value = var.environment
}

output "aws_region" {
  value = var.aws_region
}

############################################
# Network (Person A)
############################################
output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_app_subnet_ids" {
  value = module.network.private_app_subnet_ids
}

output "private_data_subnet_ids" {
  value = module.network.private_data_subnet_ids
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "route53_zone_id" {
  value = var.enable_edge ? module.edge[0].zone_id : null
}

output "route53_name_servers" {
  value = var.enable_edge ? module.edge[0].name_servers : null
}

output "cloudfront_domain_name" {
  value = var.enable_edge ? module.edge[0].cloudfront_domain_name : null
}

output "acm_certificate_arn" {
  value = var.enable_edge ? module.edge[0].acm_certificate_arn : null
}

############################################
# EKS (Person B)
############################################
output "cluster_name" {
  value = var.enable_eks ? module.eks[0].cluster_name : null
}

output "cluster_endpoint" {
  value = var.enable_eks ? module.eks[0].cluster_endpoint : null
}

output "oidc_provider_arn" {
  value = var.enable_eks ? module.eks[0].oidc_provider_arn : null
}

output "irsa_role_arns" {
  description = "Per-service IRSA role ARNs."
  value = var.enable_eks ? {
    catalog    = module.eks[0].catalog_irsa_role_arn
    auth       = module.eks[0].auth_irsa_role_arn
    cart       = module.eks[0].cart_irsa_role_arn
    admin      = module.eks[0].admin_irsa_role_arn
    checkout   = module.eks[0].checkout_irsa_role_arn
    db_migrate = module.eks[0].db_migrate_irsa_role_arn
  } : null
}

############################################
# Cognito (Person B)
############################################
output "cognito_customer_user_pool_id" {
  value = var.enable_cognito ? module.cognito[0].customer_user_pool_id : null
}

output "cognito_admin_user_pool_id" {
  value = var.enable_cognito ? module.cognito[0].admin_user_pool_id : null
}

output "cognito_customer_app_client_id" {
  value = var.enable_cognito ? module.cognito[0].customer_app_client_id : null
}

output "cognito_admin_app_client_id" {
  value = var.enable_cognito ? module.cognito[0].admin_app_client_id : null
}

############################################
# Data plane (Person C)
############################################
output "rds_writer_endpoint" {
  value = var.enable_data ? module.rds[0].writer_endpoint : null
}

output "redis_primary_endpoint" {
  value = var.enable_data ? module.redis[0].primary_endpoint : null
}

output "invoice_queue_url" {
  value = var.enable_data ? module.sqs_invoice[0].invoice_queue_url : null
}

output "invoices_bucket_name" {
  value = var.enable_data ? module.sqs_invoice[0].invoices_bucket_name : null
}

output "shared_index_secret_arn" {
  value = var.enable_data ? module.secrets[0].shared_index_secret_arn : null
}
