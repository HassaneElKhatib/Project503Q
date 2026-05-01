locals {
  is_prod = var.env == "prod"

  backup_days = var.backup_retention_days != null ? var.backup_retention_days : (local.is_prod ? 7 : 1)

  primary_instance_class = coalesce(var.instance_class, local.is_prod ? "db.r6g.large" : "db.t3.medium")
  replica_instance_class = coalesce(var.replica_instance_class, local.primary_instance_class)

  name_prefix = "${var.project_name}-${var.env}"
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.env
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

resource "random_password" "master" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Postgres access for ShopCloud services"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Postgres from app security groups"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-rds-sg" })
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name_prefix}-rds-subnet-group"
  subnet_ids = var.private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-rds-subnet-group" })
}

resource "aws_db_parameter_group" "this" {
  name        = "${local.name_prefix}-postgres-params"
  family      = "postgres16"
  description = "ShopCloud Postgres parameters"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-postgres-params" })
}

resource "aws_db_instance" "primary" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = "16.3"
  instance_class = local.primary_instance_class

  db_name  = "shopcloud"
  username = "shopcloud"
  password = random_password.master.result
  port     = 5432

  allocated_storage     = local.is_prod ? 200 : 50
  max_allocated_storage = local.is_prod ? 500 : 100
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn

  multi_az               = local.is_prod
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.this.name
  parameter_group_name   = aws_db_parameter_group.this.name

  backup_retention_period = local.backup_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection       = local.is_prod
  skip_final_snapshot       = !local.is_prod
  final_snapshot_identifier = "${local.name_prefix}-postgres-final"

  performance_insights_enabled = local.is_prod
  apply_immediately            = !local.is_prod

  enabled_cloudwatch_logs_exports     = local.is_prod ? ["postgresql", "upgrade"] : []
  iam_database_authentication_enabled = true
  auto_minor_version_upgrade          = true
  copy_tags_to_snapshot               = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-postgres" })
}

resource "aws_security_group" "rds_replica" {
  count    = local.is_prod ? 1 : 0
  provider = aws.replica

  name        = "${local.name_prefix}-rds-replica-sg"
  description = "Postgres replica access for ShopCloud services"
  vpc_id      = var.replica_vpc_id

  # Replica is in another region/VPC; primary-region SG IDs are invalid here — use replica-region SGs or VPC CIDR.
  dynamic "ingress" {
    for_each = length(var.replica_allowed_security_group_ids) > 0 ? [1] : []
    content {
      description     = "Postgres from app security groups (replica region)"
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = var.replica_allowed_security_group_ids
    }
  }

  dynamic "ingress" {
    for_each = length(var.replica_allowed_security_group_ids) == 0 ? [1] : []
    content {
      description = "Postgres from replica VPC CIDR (no replica-region SGs configured)"
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = [var.replica_ingress_cidr_ipv4]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-rds-replica-sg" })
}

resource "aws_db_subnet_group" "replica" {
  count    = local.is_prod ? 1 : 0
  provider = aws.replica

  name       = "${local.name_prefix}-rds-replica-subnet-group"
  subnet_ids = var.replica_private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-rds-replica-subnet-group" })
}

resource "aws_db_instance" "replica" {
  count    = local.is_prod ? 1 : 0
  provider = aws.replica

  identifier          = "${local.name_prefix}-postgres-replica-eu-west-1"
  replicate_source_db = aws_db_instance.primary.arn

  instance_class         = local.replica_instance_class
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.replica[0].name
  vpc_security_group_ids = [aws_security_group.rds_replica[0].id]

  storage_encrypted = true
  kms_key_id        = var.replica_kms_key_arn

  backup_retention_period = local.backup_days
  deletion_protection     = true
  skip_final_snapshot     = false

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  auto_minor_version_upgrade      = true
  copy_tags_to_snapshot           = true
  apply_immediately               = false

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-postgres-replica-eu-west-1" })
}

resource "aws_secretsmanager_secret" "database" {
  name                    = "/${var.project_name}/${var.env}/database/shared"
  recovery_window_in_days = local.is_prod ? 30 : 7
  kms_key_id              = var.kms_key_arn

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-database-secret" })
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    writer_url = "postgresql://shopcloud:${random_password.master.result}@${aws_db_instance.primary.address}:5432/shopcloud"
    reader_url = "postgresql://shopcloud:${random_password.master.result}@${try(aws_db_instance.replica[0].address, aws_db_instance.primary.address)}:5432/shopcloud"
    username   = "shopcloud"
    password   = random_password.master.result
    db_name    = "shopcloud"
    port       = 5432
  })
}
