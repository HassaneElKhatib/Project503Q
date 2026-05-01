locals {
  is_prod = var.env == "prod"

  name_prefix = "${var.project_name}-${var.env}"
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.env
      ManagedBy   = "terraform"
    },
    var.tags
  )

  redis_connect_host = coalesce(
    aws_elasticache_replication_group.this.primary_endpoint_address,
    aws_elasticache_replication_group.this.configuration_endpoint_address
  )
}

resource "random_password" "auth_token" {
  length           = 48
  special          = false
  min_lower        = 10
  min_upper        = 10
  min_numeric      = 10
  override_special = ""
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Redis access for ShopCloud services"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from app security groups"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis-sg" })
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = var.private_data_subnet_ids

  tags = local.common_tags
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "ShopCloud Redis replication group"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = local.is_prod ? "cache.r6g.large" : "cache.t3.micro"
  parameter_group_name       = local.is_prod ? "default.redis7.cluster.on" : "default.redis7"
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = var.kms_key_arn
  auth_token                 = random_password.auth_token.result
  apply_immediately          = !local.is_prod

  num_cache_clusters         = local.is_prod ? null : 1
  num_node_groups            = local.is_prod ? 1 : null
  replicas_per_node_group    = local.is_prod ? 1 : null
  multi_az_enabled           = local.is_prod
  automatic_failover_enabled = local.is_prod

  snapshot_retention_limit   = local.is_prod ? 7 : 1
  snapshot_window            = "02:00-03:00"
  maintenance_window         = "sun:03:00-sun:04:00"
  auto_minor_version_upgrade = true

  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "redis" {
  name                    = "/${var.project_name}/${var.env}/redis/shared"
  recovery_window_in_days = local.is_prod ? 30 : 7
  kms_key_id              = var.kms_key_arn

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis-secret" })
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    redis_url  = "rediss://:${random_password.auth_token.result}@${local.redis_connect_host}:6379"
    auth_token = random_password.auth_token.result
    host       = local.redis_connect_host
    port       = 6379
  })
}
