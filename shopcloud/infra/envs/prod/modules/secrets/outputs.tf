output "shared_index_secret_arn" {
  description = "Secrets Manager ARN indexing shared secret ARNs."
  value       = aws_secretsmanager_secret.index.arn
}

output "api_gateway_jwt_secret_arn" {
  description = "Secrets Manager ARN for api-gateway JWT signing secret."
  value       = aws_secretsmanager_secret.api_gateway_jwt.arn
}
