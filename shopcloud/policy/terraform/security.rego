package terraform.security

# RDS instances must have storage_encrypted = true
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	not resource.change.after.storage_encrypted
	msg := sprintf("RDS instance %s must have storage_encrypted=true", [resource.address])
}

# RDS instances must not be publicly accessible
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	resource.change.after.publicly_accessible == true
	msg := sprintf("RDS instance %s must not be publicly accessible", [resource.address])
}

# RDS instances must have a KMS key for storage encryption
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	not resource.change.after.kms_key_id
	msg := sprintf("RDS instance %s must specify kms_key_id", [resource.address])
}

# Secrets Manager secrets must be encrypted with a customer-managed KMS key
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_secretsmanager_secret"
	is_creating(resource)
	not resource.change.after.kms_key_id
	msg := sprintf("Secret %s must use a customer-managed KMS key", [resource.address])
}

# ElastiCache replication groups must enable encryption at rest
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_elasticache_replication_group"
	is_creating(resource)
	not resource.change.after.at_rest_encryption_enabled
	msg := sprintf("ElastiCache %s must enable at_rest_encryption_enabled", [resource.address])
}

# ElastiCache replication groups must enable encryption in transit
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_elasticache_replication_group"
	is_creating(resource)
	not resource.change.after.transit_encryption_enabled
	msg := sprintf("ElastiCache %s must enable transit_encryption_enabled", [resource.address])
}

# S3 public-access blocks must block all four flags
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_s3_bucket_public_access_block"
	is_creating(resource)
	not all_blocked(resource)
	msg := sprintf("S3 public access block %s must block all four flags", [resource.address])
}

# SQS queues must use a KMS master key
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_sqs_queue"
	is_creating(resource)
	not resource.change.after.kms_master_key_id
	msg := sprintf("SQS queue %s must specify kms_master_key_id", [resource.address])
}

# Security groups must not allow 0.0.0.0/0 ingress
deny[msg] {
	resource := input.resource_changes[_]
	resource.type == "aws_security_group"
	is_creating(resource)
	ingress := resource.change.after.ingress[_]
	ingress.cidr_blocks[_] == "0.0.0.0/0"
	msg := sprintf("Security group %s must not allow 0.0.0.0/0 ingress", [resource.address])
}

# Block destroys/replacements of critical infra.
# We allow aws_secretsmanager_secret_version replacement because secret version
# rotation is expected and non-destructive to core infrastructure.
deny[msg] {
	resource := input.resource_changes[_]
	has_delete(resource)
	resource.type != "aws_secretsmanager_secret_version"
	is_protected_destroy_type(resource.type)
	msg := sprintf("Destroy/replacement is blocked for critical resource %s (%s) actions=%v", [resource.address, resource.type, resource.change.actions])
}

deny[msg] {
	resource := input.resource_changes[_]
	has_delete(resource)
	resource.type != "aws_secretsmanager_secret_version"
	is_admin_or_vpn_resource(resource.address)
	msg := sprintf("Destroy/replacement is blocked for admin/VPN resource %s actions=%v", [resource.address, resource.change.actions])
}

is_creating(resource) {
	resource.change.actions[_] == "create"
}

is_creating(resource) {
	resource.change.actions[_] == "update"
}

has_delete(resource) {
	resource.change.actions[_] == "delete"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_db_instance"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_eks_node_group"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_eks_cluster"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_cloudfront_distribution"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_route53_zone"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_ec2_client_vpn_endpoint"
}

is_protected_destroy_type(resource_type) {
	resource_type == "aws_cognito_user_pool"
}

is_admin_or_vpn_resource(address) {
	contains(address, "module.admin_private_access")
}

is_admin_or_vpn_resource(address) {
	contains(address, "module.vpn")
}

all_blocked(resource) {
	resource.change.after.block_public_acls == true
	resource.change.after.block_public_policy == true
	resource.change.after.ignore_public_acls == true
	resource.change.after.restrict_public_buckets == true
}
