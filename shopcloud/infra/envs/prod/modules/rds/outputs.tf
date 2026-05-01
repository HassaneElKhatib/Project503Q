output "writer_endpoint" {
  description = "Primary writer endpoint for Postgres."
  value       = aws_db_instance.primary.address
}

output "reader_endpoint" {
  description = "Reader endpoint for Postgres."
  value       = try(aws_db_instance.replica[0].address, aws_db_instance.primary.address)
}

output "replica_endpoint" {
  description = "Cross-region replica endpoint for Postgres (prod)."
  value       = try(aws_db_instance.replica[0].address, null)
}

output "secret_arn_database" {
  description = "Secrets Manager ARN containing DB URLs."
  value       = aws_secretsmanager_secret.database.arn
}
