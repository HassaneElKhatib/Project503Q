############################################
# Top-level identity / region
############################################
variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project prefix for naming and tagging."
  type        = string
  default     = "shopcloud"
}

variable "aws_region" {
  description = "Primary AWS region."
  type        = string
  default     = "eu-central-1"
}

variable "replica_aws_region" {
  description = "Cross-region read replica region (prod-only feature; dev still requires a value for provider config)."
  type        = string
  default     = "eu-west-1"
}

############################################
# Network (Person A)
############################################
variable "vpc_cidr" {
  description = "Must not overlap other VPCs in this account."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.0.0/20", "10.20.16.0/20"]
}

variable "private_app_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.32.0/20", "10.20.48.0/20"]
}

variable "private_data_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.64.0/20", "10.20.80.0/20"]
}

variable "nat_gateway_count" {
  description = "Dev defaults to 1 NAT gateway."
  type        = number
  default     = 1
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
  description = "Create Route53 + ACM + CloudFront + WAF (set false for VPC+ECR only)."
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Public DNS for this env's hosted zone (e.g. dev.shopcloud.example.com)."
  type        = string
  default     = "dev.shopcloud.example.com"
}

variable "origin_domain_name" {
  description = "ALB DNS used as CloudFront origin (placeholder until ingress exists)."
  type        = string
  default     = "k8s-shopcloud-public-placeholder.eu-central-1.elb.amazonaws.com"
}

############################################
# EKS (Person B)
############################################
variable "enable_eks" {
  description = "Stand up the EKS cluster + node groups in this env."
  type        = bool
  default     = true
}

variable "kubernetes_version" {
  type    = string
  default = "1.29"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
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
  default = 4
}

variable "vpc_cni_enable_prefix_delegation" {
  description = "Register vpc-cni as an EKS managed add-on with IPv4 prefix delegation for higher pod counts on small instances (e.g. t3.micro), without larger instance types."
  type        = bool
  default     = true
}

variable "enable_helm_addons" {
  description = "Wire IRSA roles inside the EKS module for ALB Controller / Cluster Autoscaler / External Secrets, then install the helm releases via the eks_helm_addons module."
  type        = bool
  default     = true
}

variable "enable_external_secrets" {
  description = "Install external-secrets Helm chart in dev."
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaler" {
  description = "Install cluster-autoscaler Helm chart in dev."
  type        = bool
  default     = true
}

############################################
# Cognito (Person B)
############################################
variable "enable_cognito" {
  type    = bool
  default = true
}

variable "cookie_domain" {
  description = "Cookie domain for the auth service."
  type        = string
  default     = ".dev.shopcloud.example.com"
}

variable "customer_domain_prefix" {
  type    = string
  default = "shopcloud-dev-customer"
}

variable "admin_domain_prefix" {
  type    = string
  default = "shopcloud-dev-admin"
}

variable "customer_callback_url" {
  type    = string
  default = "https://dev.shopcloud.example.com/auth/callback"
}

variable "customer_logout_url" {
  type    = string
  default = "https://dev.shopcloud.example.com/"
}

variable "admin_callback_url" {
  type    = string
  default = "https://admin.dev.internal.shopcloud.example.com/auth/callback"
}

variable "admin_logout_url" {
  type    = string
  default = "https://admin.dev.internal.shopcloud.example.com/"
}

############################################
# Data plane (Person C)
############################################
variable "enable_data" {
  description = "Stand up RDS + Redis + SQS-invoice + Secrets."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "KMS CMK ARN used by RDS / Redis / SQS / Secrets. Required when enable_data=true."
  type        = string
  default     = null
}

variable "rds_backup_retention_days" {
  type    = number
  default = 1 # dev
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "rds_replica_instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "ses_from_address" {
  type    = string
  default = "noreply@dev.shopcloud.example.com"
}

variable "lambda_zip_path" {
  description = "Built invoice-worker artifact relative to this env root."
  type        = string
  default     = "../../../services/invoice-worker/dist/invoice-worker.zip"
}

# Replica region inputs are required by the rds module signature even
# in dev where the replica is effectively unused; we point at default
# VPC values that AWS auto-creates so a `terraform apply` doesn't
# require humans to wire two VPCs for a dev-only run.
variable "replica_vpc_id" {
  type    = string
  default = ""
}

variable "replica_private_data_subnet_ids" {
  type    = list(string)
  default = []
}

variable "replica_kms_key_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
