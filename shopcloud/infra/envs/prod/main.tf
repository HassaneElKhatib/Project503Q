############################################
# Prod environment root
# Wires Person A network/edge/ecr, Person B eks/cognito,
# and Person C rds/redis/sqs-invoice/secrets into a single stack.
############################################

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# us-east-1 alias is required by the edge module (CloudFront cert).
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Replica alias is consumed by the rds module signature.
provider "aws" {
  alias  = "replica"
  region = var.replica_aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "helm" {
  alias = "eks"

  kubernetes {
    host                   = try(module.eks[0].cluster_endpoint, null)
    cluster_ca_certificate = try(base64decode(module.eks[0].cluster_certificate_authority_data), null)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", try(module.eks[0].cluster_name, ""), "--region", var.aws_region]
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(sort(data.aws_availability_zones.available.names), 0, 2)

  eks_cluster_name = "${local.name_prefix}-eks"

  use_private_admin_dns = (
    var.enable_private_admin_access &&
    var.enable_cognito &&
    var.enable_edge &&
    var.enable_eks
  )

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

############################################
# Person A — Network, ECR, Edge
############################################
module "network" {
  source = "./modules/network"

  name_prefix               = local.name_prefix
  vpc_cidr                  = var.vpc_cidr
  azs                       = local.azs
  public_subnet_cidrs       = var.public_subnet_cidrs
  private_app_subnet_cidrs  = var.private_app_subnet_cidrs
  private_data_subnet_cidrs = var.private_data_subnet_cidrs
  nat_gateway_count         = var.nat_gateway_count
}

module "ecr" {
  source = "./modules/ecr"

  name_prefix  = local.name_prefix
  repositories = var.ecr_repositories
}

module "edge" {
  source = "./modules/edge"
  count  = var.enable_edge ? 1 : 0

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }

  name_prefix        = local.name_prefix
  domain_name        = var.domain_name
  origin_domain_name = var.origin_domain_name
}

module "vpn" {
  source = "./modules/vpn"
  count  = var.enable_client_vpn ? 1 : 0

  name_prefix                       = local.name_prefix
  vpc_id                            = module.network.vpc_id
  vpc_cidr                          = var.vpc_cidr
  association_subnet_ids            = module.network.private_app_subnet_ids
  server_certificate_arn            = var.client_vpn_server_certificate_arn
  client_root_certificate_chain_arn = var.client_vpn_client_root_certificate_chain_arn
  client_cidr_block                 = var.client_vpn_client_cidr
  split_tunnel                      = var.client_vpn_split_tunnel
  saml_provider_arn                 = var.client_vpn_saml_provider_arn
  self_service_saml_provider_arn    = var.client_vpn_self_service_saml_provider_arn
  enable_federated_authentication   = var.client_vpn_enable_saml_federation
  saml_metadata_document            = var.client_vpn_saml_metadata_document
  tags                              = local.common_tags
}

module "admin_private_access" {
  source = "./modules/admin_private_access"
  count  = local.use_private_admin_dns ? 1 : 0

  name_prefix    = local.name_prefix
  domain_name    = var.domain_name
  vpc_id         = module.network.vpc_id
  public_zone_id = module.edge[0].zone_id
  cluster_name   = local.eks_cluster_name
  record_label   = var.admin_private_dns_record_label
  tags           = local.common_tags
}

############################################
# Person B — Cognito, EKS, Helm add-ons
############################################
module "cognito" {
  source = "./modules/cognito"
  count  = var.enable_cognito ? 1 : 0

  environment            = var.environment
  region                 = var.aws_region
  customer_domain_prefix = var.customer_domain_prefix
  admin_domain_prefix    = var.admin_domain_prefix
  customer_callback_url  = var.customer_callback_url
  customer_logout_url    = var.customer_logout_url
  admin_callback_url = local.use_private_admin_dns ? (
    "https://${module.admin_private_access[0].admin_fqdn}/auth/admin/callback"
  ) : var.admin_callback_url
  admin_logout_url = local.use_private_admin_dns ? (
    "https://${module.admin_private_access[0].admin_fqdn}/"
  ) : var.admin_logout_url
  cookie_domain = var.cookie_domain
  kms_key_id    = var.kms_key_arn
  tags          = local.common_tags
}

module "eks" {
  source = "./modules/eks"
  count  = var.enable_eks ? 1 : 0

  cluster_name                  = local.eks_cluster_name
  aws_region                    = var.aws_region
  kubernetes_version            = var.kubernetes_version
  enable_kms_secrets_encryption = true
  private_subnet_ids            = module.network.private_app_subnet_ids
  node_instance_types           = var.node_instance_types
  node_desired_size             = var.node_desired_size
  node_min_size                 = var.node_min_size
  node_max_size                 = var.node_max_size

  vpc_cni_enable_prefix_delegation = var.vpc_cni_enable_prefix_delegation

  enable_irsa        = true
  enable_helm_addons = var.enable_helm_addons

  # Wire IRSA-readable secrets directly from the producing modules.
  secret_arn_shared_database  = var.enable_data ? module.rds[0].secret_arn_database : null
  secret_arn_shared_redis     = var.enable_data ? module.redis[0].secret_arn_redis : null
  secret_arn_invoice_queue    = var.enable_data ? module.sqs_invoice[0].secret_arn_invoice_queue : null
  secret_arn_cognito_customer = var.enable_cognito ? module.cognito[0].customer_cognito_secret_arn : null
  secret_arn_cognito_admin    = var.enable_cognito ? module.cognito[0].admin_cognito_secret_arn : null
  invoice_queue_arn           = var.enable_data ? module.sqs_invoice[0].invoice_queue_arn : null

  external_secrets_allowed_secret_arns = compact(concat(
    var.enable_data ? [
      module.rds[0].secret_arn_database,
      module.redis[0].secret_arn_redis,
      module.sqs_invoice[0].secret_arn_invoice_queue,
      module.secrets[0].api_gateway_jwt_secret_arn,
      module.secrets[0].api_gateway_smtp_secret_arn,
    ] : [],
    var.enable_data && var.enable_cognito ? [
      module.cognito[0].customer_cognito_secret_arn,
      module.cognito[0].admin_cognito_secret_arn,
    ] : [],
  ))
  external_secrets_kms_key_arns = var.kms_key_arn != null ? [var.kms_key_arn] : []

  tags = local.common_tags
}

module "eks_helm_addons" {
  source = "./modules/eks_helm_addons"
  count  = var.enable_eks && var.enable_helm_addons ? 1 : 0

  providers = {
    helm = helm.eks
  }

  cluster_name                = module.eks[0].cluster_name
  cluster_endpoint            = module.eks[0].cluster_endpoint
  cluster_ca_data             = module.eks[0].cluster_certificate_authority_data
  aws_region                  = var.aws_region
  vpc_id                      = module.network.vpc_id
  alb_controller_role_arn     = module.eks[0].aws_load_balancer_controller_irsa_role_arn
  cluster_autoscaler_role_arn = module.eks[0].cluster_autoscaler_irsa_role_arn
  external_secrets_role_arn   = module.eks[0].external_secrets_irsa_role_arn
}

############################################
# Person C — RDS, Redis, SQS+Lambda, Secrets
############################################
module "rds" {
  source = "./modules/rds"
  count  = var.enable_data ? 1 : 0

  providers = {
    aws         = aws
    aws.replica = aws.replica
  }

  project_name                    = var.project_name
  env                             = var.environment
  vpc_id                          = module.network.vpc_id
  private_data_subnet_ids         = module.network.private_data_subnet_ids
  kms_key_arn                     = var.kms_key_arn
  replica_vpc_id                  = var.replica_vpc_id
  replica_private_data_subnet_ids = var.replica_private_data_subnet_ids
  replica_kms_key_arn             = var.replica_kms_key_arn
  # Pods/nodes use the EKS cluster security group; without this, Postgres is unreachable from the app VPC.
  allowed_security_group_ids         = var.enable_eks ? [module.eks[0].node_security_group_id] : []
  backup_retention_days              = var.rds_backup_retention_days
  replica_allowed_security_group_ids = []
  replica_ingress_cidr_ipv4          = "172.31.0.0/16"
  instance_class                     = var.rds_instance_class
  replica_instance_class             = var.rds_replica_instance_class

  tags = local.common_tags
}

module "redis" {
  source = "./modules/redis"
  count  = var.enable_data ? 1 : 0

  project_name               = var.project_name
  env                        = var.environment
  vpc_id                     = module.network.vpc_id
  private_data_subnet_ids    = module.network.private_data_subnet_ids
  kms_key_arn                = var.kms_key_arn
  allowed_security_group_ids = var.enable_eks ? [module.eks[0].node_security_group_id] : []

  tags = local.common_tags
}

module "sqs_invoice" {
  source = "./modules/sqs-invoice"
  count  = var.enable_data ? 1 : 0

  project_name     = var.project_name
  env              = var.environment
  aws_region       = var.aws_region
  kms_key_arn      = var.kms_key_arn
  ses_from_address = var.ses_from_address
  lambda_zip_path  = var.lambda_zip_path

  tags = local.common_tags
}

module "secrets" {
  source = "./modules/secrets"
  count  = var.enable_data ? 1 : 0

  project_name             = var.project_name
  env                      = var.environment
  kms_key_arn              = var.kms_key_arn
  aws_region               = var.aws_region
  smtp_from_address        = var.ses_from_address
  database_secret_arn      = module.rds[0].secret_arn_database
  redis_secret_arn         = module.redis[0].secret_arn_redis
  invoice_queue_secret_arn = module.sqs_invoice[0].secret_arn_invoice_queue

  tags = local.common_tags
}
