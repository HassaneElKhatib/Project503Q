variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
}

variable "env" {
  description = "Deployment environment (dev/prod)."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where DB security group is created."
  type        = string
}

variable "private_data_subnet_ids" {
  description = "Private data subnet IDs for RDS subnet group."
  type        = list(string)
}

variable "kms_key_arn" {
  description = "KMS key ARN for RDS encryption."
  type        = string
}

variable "allowed_security_group_ids" {
  description = "Security groups allowed to reach Postgres (must exist in the primary region VPC)."
  type        = list(string)
  default     = []
}

variable "backup_retention_days" {
  description = "Backup retention (days) for primary and replica. Default: 7 prod / 1 dev. Use 1 if AWS returns FreeTierRestrictionError on backup retention."
  type        = number
  default     = null
}

variable "replica_allowed_security_group_ids" {
  description = "Security groups in the replica region VPC allowed to reach the read replica. Cannot use primary-region SG IDs. Empty = allow replica_ingress_cidr_ipv4 instead."
  type        = list(string)
  default     = []
}

variable "replica_ingress_cidr_ipv4" {
  description = "When replica_allowed_security_group_ids is empty, allow Postgres from this CIDR (e.g. replica VPC CIDR)."
  type        = string
  default     = "172.31.0.0/16"
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}

variable "replica_vpc_id" {
  description = "VPC ID in replica region for cross-region read replica networking."
  type        = string
}

variable "replica_private_data_subnet_ids" {
  description = "Private data subnet IDs in replica region for cross-region read replica."
  type        = list(string)
}

variable "replica_kms_key_arn" {
  description = "KMS key ARN in replica region for cross-region read replica encryption."
  type        = string
}

variable "instance_class" {
  description = "Primary RDS instance class. Default db.r6g.large (prod) / db.t3.medium (dev). Use db.t4g.medium or db.t3.medium if AWS returns FreeTierRestrictionError."
  type        = string
  default     = null
}

variable "replica_instance_class" {
  description = "Read replica instance class. Defaults to same as primary when unset."
  type        = string
  default     = null
}
