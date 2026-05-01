resource "aws_cognito_user_pool" "customer" {
  name = "shopcloud-${var.environment}-customer-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 10
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  tags = var.tags
}

resource "aws_cognito_user_pool_client" "customer" {
  name         = "shopcloud-${var.environment}-customer-client"
  user_pool_id = aws_cognito_user_pool.customer.id

  generate_secret = false

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  callback_urls = [var.customer_callback_url]
  logout_urls   = [var.customer_logout_url]

  supported_identity_providers = ["COGNITO"]

  prevent_user_existence_errors = "ENABLED"
}

resource "aws_cognito_user_pool_domain" "customer" {
  domain       = var.customer_domain_prefix
  user_pool_id = aws_cognito_user_pool.customer.id
}

resource "aws_cognito_user_pool" "admin" {
  name = "shopcloud-${var.environment}-admin-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  mfa_configuration = "ON"

  software_token_mfa_configuration {
    enabled = true
  }

  tags = var.tags
}

resource "aws_cognito_user_pool_client" "admin" {
  name         = "shopcloud-${var.environment}-admin-client"
  user_pool_id = aws_cognito_user_pool.admin.id

  generate_secret = false

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  callback_urls = [var.admin_callback_url]
  logout_urls   = [var.admin_logout_url]

  supported_identity_providers = ["COGNITO"]

  prevent_user_existence_errors = "ENABLED"
}

resource "aws_cognito_user_pool_domain" "admin" {
  domain       = var.admin_domain_prefix
  user_pool_id = aws_cognito_user_pool.admin.id
}

resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.admin.id
  description  = "Admin users for ShopCloud inventory management."
}