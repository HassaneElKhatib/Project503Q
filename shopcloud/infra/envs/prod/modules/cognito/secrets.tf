resource "random_password" "state_signing_key" {
  length  = 32
  special = true
}

resource "random_password" "admin_state_signing_key" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "customer_cognito" {
  name        = "/shopcloud/${var.environment}/cognito/customer"
  description = "Customer Cognito configuration for ShopCloud ${var.environment}."

  kms_key_id = var.kms_key_id

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "customer_cognito" {
  secret_id = aws_secretsmanager_secret.customer_cognito.id

  secret_string = jsonencode({
    user_pool_id        = aws_cognito_user_pool.customer.id
    app_client_id       = aws_cognito_user_pool_client.customer.id
    region              = var.region
    domain              = "${aws_cognito_user_pool_domain.customer.domain}.auth.${var.region}.amazoncognito.com"
    callback_url        = var.customer_callback_url
    logout_redirect_url = var.customer_logout_url
    cookie_domain       = var.cookie_domain
    state_signing_key   = random_password.state_signing_key.result
  })
}

resource "aws_secretsmanager_secret" "admin_cognito" {
  name        = "/shopcloud/${var.environment}/cognito/admin"
  description = "Admin Cognito configuration for ShopCloud ${var.environment}."

  kms_key_id = var.kms_key_id

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "admin_cognito" {
  secret_id = aws_secretsmanager_secret.admin_cognito.id

  secret_string = jsonencode({
    user_pool_id        = aws_cognito_user_pool.admin.id
    app_client_id       = aws_cognito_user_pool_client.admin.id
    region              = var.region
    domain              = "${aws_cognito_user_pool_domain.admin.domain}.auth.${var.region}.amazoncognito.com"
    callback_url        = var.admin_callback_url
    logout_redirect_url = var.admin_logout_url
    cookie_domain       = var.cookie_domain
    state_signing_key   = random_password.admin_state_signing_key.result
  })
}