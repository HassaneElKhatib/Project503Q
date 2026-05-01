output "primary_endpoint" {
  description = "Redis hostname (configuration endpoint in cluster mode, else primary)."
  value = coalesce(
    aws_elasticache_replication_group.this.primary_endpoint_address,
    aws_elasticache_replication_group.this.configuration_endpoint_address
  )
}

output "secret_arn_redis" {
  description = "Secrets Manager ARN containing Redis URL."
  value       = aws_secretsmanager_secret.redis.arn
}
