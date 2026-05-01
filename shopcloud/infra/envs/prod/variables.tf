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

variable "enable_edge" {
  type    = bool
  default = true
}

variable "domain_name" {
  type    = string
  default = "shopcloud.example.com"
}

variable "origin_domain_name" {
  type    = string
  default = "k8s-shopcloud-public-placeholder.eu-central-1.elb.amazonaws.com"
}

variable "enable_eks" {
  type    = bool
  default = true
}

variable "kubernetes_version" {
  type    = string
  default = "1.29"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "node_desired_size" {
  type    = number
  default = 3
}

variable "node_min_size" {
  type    = number
  default = 3
}

variable "node_max_size" {
  type    = number
  default = 6
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

variable "enable_cognito" {
  type    = bool
  default = true
}

variable "cookie_domain" {
  type    = string
  default = ".shopcloud.example.com"
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
  default = "https://shopcloud.example.com/auth/callback"
}

variable "customer_logout_url" {
  type    = string
  default = "https://shopcloud.example.com/"
}

variable "admin_callback_url" {
  type    = string
  default = "https://admin.internal.shopcloud.example.com/auth/callback"
}

variable "admin_logout_url" {
  type    = string
  default = "https://admin.internal.shopcloud.example.com/"
}

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
  default = 7
}

variable "rds_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "rds_replica_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "ses_from_address" {
  type    = string
  default = "noreply@shopcloud.example.com"
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
