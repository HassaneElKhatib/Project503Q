output "shared_index_secret_arn" {
  description = "Secrets Manager ARN indexing shared secret ARNs."
  value       = aws_secretsmanager_secret.index.arn
}
