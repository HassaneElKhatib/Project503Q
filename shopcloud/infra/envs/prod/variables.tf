############################################
# Top-level identity / region
############################################
variable "environment" {
  type    = string
  default = "prod"
}

variable "project_name" {
  type    = string
  default = "shopcloud"
}

variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "replica_aws_region" {
  description = "Cross-region replica region (always required in prod)."
  type        = string
  default     = "eu-west-1"
}

############################################
# Network (Person A)
############################################
variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.30.0.0/20", "10.30.16.0/20"]
}

variable "private_app_subnet_cidrs" {
  type    = list(string)
  default = ["10.30.32.0/20", "10.30.48.0/20"]
}

variable "private_data_subnet_cidrs" {
  type    = list(string)
  default = ["10.30.64.0/20", "10.30.80.0/20"]
}

variable "nat_gateway_count" {
  description = "Prod uses one NAT per AZ (high availability)."
  type        = number
  default     = 2
}

############################################
# ECR (Person A)
############################################
variable "ecr_repositories" {
  type = list(string)
  default = [
    "catalog",
    "auth",
    "cart",
    "admin",
    "checkout",
    "api-gateway",
    "customer-web",
  ]
}

############################################
# Edge / DNS (Person A)
############################################
variable "enable_edge" {
  type    = bool
  default = true
}

variable "enable_client_vpn" {
  description = "Enable AWS Client VPN endpoint."
  type        = bool
  default     = true
}

variable "client_vpn_server_certificate_arn" {
  description = "ACM certificate ARN used by the Client VPN endpoint."
  type        = string
  default     = null
}

variable "client_vpn_client_root_certificate_chain_arn" {
  description = "ACM certificate chain ARN used for client certificate authentication."
  type        = string
  default     = null
}

variable "client_vpn_client_cidr" {
  description = "CIDR assigned to VPN clients."
  type        = string
  default     = "10.222.0.0/22"
}

variable "client_vpn_split_tunnel" {
  description = "If true, only VPC routes go through the VPN."
  type        = bool
  default     = true
}

variable "client_vpn_saml_provider_arn" {
  description = "Optional IAM SAML provider ARN for federated auth (MFA-capable)."
  type        = string
  default     = null
}

variable "client_vpn_self_service_saml_provider_arn" {
  description = "Optional IAM SAML provider ARN for Client VPN self-service portal."
  type        = string
  default     = null
}

variable "client_vpn_enable_saml_federation" {
  description = "Add SAML IdP authentication alongside client certificates. MFA is enforced by your IdP during SAML sign-in (Okta/Azure AD/IAM Identity Center)."
  type        = bool
  default     = false
}

variable "client_vpn_saml_metadata_document" {
  description = "Optional SAML metadata XML for VPN federation."
  type        = string
  default     = null
  sensitive   = true
}

variable "enable_private_admin_access" {
  description = "Private Route53 record + ACM for internal admin ALB."
  type        = bool
  default     = true
}

variable "admin_private_dns_record_label" {
  description = "Hostname label under var.domain_name (e.g. priv-admin)."
  type        = string
  default     = "priv-admin"
}

variable "domain_name" {
  type    = string
  default = "www.welovedassouki.store"
}

variable "origin_domain_name" {
  type    = string
  default = "k8s-shopcloudpublic-3976a6d8dc-1488320077.eu-central-1.elb.amazonaws.com"
}

############################################
# EKS (Person B)
############################################
variable "enable_eks" {
  type    = bool
  default = true
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.micro"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 5
}

variable "vpc_cni_enable_prefix_delegation" {
  description = "Register vpc-cni as an EKS managed add-on with IPv4 prefix delegation so small instances (e.g. t3.micro) can schedule far more than the default ~4 pods per node, without using non-free-tier instance sizes."
  type        = bool
  default     = true
}

variable "enable_helm_addons" {
  type    = bool
  default = true
}

############################################
# Cognito (Person B)
############################################
variable "enable_cognito" {
  type    = bool
  default = true
}

variable "cookie_domain" {
  type    = string
  default = ".www.welovedassouki.store"
}

variable "customer_domain_prefix" {
  type    = string
  default = "shopcloud-prod-customer"
}

variable "admin_domain_prefix" {
  type    = string
  default = "shopcloud-prod-admin"
}

variable "customer_callback_url" {
  type    = string
  default = "https://www.welovedassouki.store/auth/callback"
}

variable "customer_logout_url" {
  type    = string
  default = "https://www.welovedassouki.store/"
}

variable "admin_callback_url" {
  type    = string
  default = "https://priv-admin.www.welovedassouki.store/auth/admin/callback"
}

variable "admin_logout_url" {
  type    = string
  default = "https://priv-admin.www.welovedassouki.store/"
}

############################################
# Data plane (Person C)
############################################
variable "enable_data" {
  type    = bool
  default = true
}

variable "kms_key_arn" {
  description = "Primary-region KMS CMK ARN. Required when enable_data=true."
  type        = string
  default     = null
}

variable "rds_backup_retention_days" {
  type    = number
  default = 1
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "rds_replica_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "ses_from_address" {
  type    = string
  default = "noreply@www.welovedassouki.store"
}

variable "lambda_zip_path" {
  type    = string
  default = "../../../services/invoice-worker/dist/invoice-worker.zip"
}

variable "replica_vpc_id" {
  type = string
}

variable "replica_private_data_subnet_ids" {
  type = list(string)
}

variable "replica_kms_key_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
