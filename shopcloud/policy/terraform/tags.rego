package terraform.tags

required_tags := ["Project", "Environment", "ManagedBy"]

taggable_types := {
	"aws_db_instance",
	"aws_db_subnet_group",
	"aws_db_parameter_group",
	"aws_elasticache_replication_group",
	"aws_elasticache_subnet_group",
	"aws_s3_bucket",
	"aws_sqs_queue",
	"aws_secretsmanager_secret",
	"aws_lambda_function",
	"aws_security_group",
	"aws_iam_role",
	"aws_cloudwatch_log_group",
}

warn[msg] {
	resource := input.resource_changes[_]
	taggable_types[resource.type]
	resource.change.actions[_] == "create"
	tag := required_tags[_]
	not has_tag(resource, tag)
	msg := sprintf("Resource %s missing required tag '%s'", [resource.address, tag])
}

has_tag(resource, tag) {
	tags := resource.change.after.tags
	tags[tag]
}

has_tag(resource, tag) {
	tags := resource.change.after.tags_all
	tags[tag]
}
