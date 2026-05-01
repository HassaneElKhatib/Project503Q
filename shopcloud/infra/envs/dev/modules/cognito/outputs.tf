output "customer_user_pool_id" {
  value = aws_cognito_user_pool.customer.id
}

output "admin_user_pool_id" {
  value = aws_cognito_user_pool.admin.id
}

output "customer_app_client_id" {
  value = aws_cognito_user_pool_client.customer.id
}

output "admin_app_client_id" {
  value = aws_cognito_user_pool_client.admin.id
}

output "customer_cognito_secret_arn" {
  value = aws_secretsmanager_secret.customer_cognito.arn
}

output "admin_cognito_secret_arn" {
  value = aws_secretsmanager_secret.admin_cognito.arn
}