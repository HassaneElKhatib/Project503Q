package terraform.security

import future.keywords.in
import future.keywords.if

# RDS instances must have storage_encrypted = true
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	not resource.change.after.storage_encrypted
	msg := sprintf("RDS instance %s must have storage_encrypted=true", [resource.address])
}

# RDS instances must not be publicly accessible
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	resource.change.after.publicly_accessible == true
	msg := sprintf("RDS instance %s must not be publicly accessible", [resource.address])
}

# RDS instances must have a KMS key for storage encryption
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_db_instance"
	is_creating(resource)
	not resource.change.after.kms_key_id
	msg := sprintf("RDS instance %s must specify kms_key_id", [resource.address])
}

# Secrets Manager secrets must be encrypted with a customer-managed KMS key
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_secretsmanager_secret"
	is_creating(resource)
	not resource.change.after.kms_key_id
	msg := sprintf("Secret %s must use a customer-managed KMS key", [resource.address])
}

# ElastiCache replication groups must enable encryption at rest
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_elasticache_replication_group"
	is_creating(resource)
	not resource.change.after.at_rest_encryption_enabled
	msg := sprintf("ElastiCache %s must enable at_rest_encryption_enabled", [resource.address])
}

# ElastiCache replication groups must enable encryption in transit
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_elasticache_replication_group"
	is_creating(resource)
	not resource.change.after.transit_encryption_enabled
	msg := sprintf("ElastiCache %s must enable transit_encryption_enabled", [resource.address])
}

# S3 public-access blocks must block all four flags
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_s3_bucket_public_access_block"
	is_creating(resource)
	not all_blocked(resource)
	msg := sprintf("S3 public access block %s must block all four flags", [resource.address])
}

# SQS queues must use a KMS master key
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_sqs_queue"
	is_creating(resource)
	not resource.change.after.kms_master_key_id
	msg := sprintf("SQS queue %s must specify kms_master_key_id", [resource.address])
}

# Security groups must not allow 0.0.0.0/0 ingress
deny contains msg if {
	resource := input.resource_changes[_]
	resource.type == "aws_security_group"
	is_creating(resource)
	ingress := resource.change.after.ingress[_]
	ingress.cidr_blocks[_] == "0.0.0.0/0"
	msg := sprintf("Security group %s must not allow 0.0.0.0/0 ingress", [resource.address])
}

is_creating(resource) if {
	resource.change.actions[_] == "create"
}

is_creating(resource) if {
	resource.change.actions[_] == "update"
}

all_blocked(resource) if {
	resource.change.after.block_public_acls == true
	resource.change.after.block_public_policy == true
	resource.change.after.ignore_public_acls == true
	resource.change.after.restrict_public_buckets == true
}
