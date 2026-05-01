data "aws_caller_identity" "current" {}

data "aws_subnet" "first_private" {
  id = var.private_subnet_ids[0]
}
