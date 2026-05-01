variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
}

variable "aws_region" {
  description = "AWS region (used by Helm provider exec auth and IAM policies)."
  type        = string
}

variable "enable_kms_secrets_encryption" {
  description = "Enable envelope encryption for Kubernetes Secrets at rest using a customer-managed KMS key."
  type        = bool
  default     = true
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster."
  type        = string
  default     = "1.29"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs where EKS worker nodes will run."
  type        = list(string)
}

variable "node_instance_types" {
  description = "EC2 instance types for the EKS managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

variable "vpc_cni_enable_prefix_delegation" {
  description = "When true, manage vpc-cni as an EKS add-on with ENABLE_PREFIX_DELEGATION for higher pod counts on small instances (e.g. t3.micro)."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources."
  type        = map(string)
  default     = {}
}

variable "enable_irsa" {
  description = "Whether to create IRSA roles for Kubernetes service accounts."
  type        = bool
  default     = false
}

variable "secret_arn_shared_database" {
  description = "Secrets Manager ARN for the shared database secret."
  type        = string
  default     = null
}

variable "secret_arn_shared_redis" {
  description = "Secrets Manager ARN for the shared Redis secret."
  type        = string
  default     = null
}

variable "secret_arn_cognito_customer" {
  description = "Secrets Manager ARN for the customer Cognito secret."
  type        = string
  default     = null
}

variable "secret_arn_cognito_admin" {
  description = "Secrets Manager ARN for the admin Cognito secret."
  type        = string
  default     = null
}

variable "secret_arn_invoice_queue" {
  description = "Secrets Manager ARN for the invoice queue secret."
  type        = string
  default     = null
}

variable "invoice_queue_arn" {
  description = "SQS invoice queue ARN. Checkout can send messages only to this queue."
  type        = string
  default     = null
}

variable "service_account_namespace" {
  description = "Kubernetes namespace where app service accounts live."
  type        = string
  default     = "app"
}

variable "enable_helm_addons" {
  description = "Create IAM roles for ALB Controller, Cluster Autoscaler, External Secrets (Helm charts via module eks_helm_addons)."
  type        = bool
  default     = false
}

variable "external_secrets_allowed_secret_arns" {
  description = "Secrets Manager ARNs External Secrets Operator may read. If empty with Helm add-ons, uses '*' (tighten when secrets ARNs are known)."
  type        = list(string)
  default     = []
}

variable "external_secrets_kms_key_arns" {
  description = "Optional KMS key ARNs for secrets encrypted with CMKs."
  type        = list(string)
  default     = []
}
