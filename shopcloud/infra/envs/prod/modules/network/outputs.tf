output "vpc_id" {
  description = "VPC ID used by downstream modules"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = values(aws_subnet.public)[*].id
}

output "private_app_subnet_ids" {
  description = "Private application subnet IDs"
  value       = values(aws_subnet.private_app)[*].id
}

output "private_data_subnet_ids" {
  description = "Private data subnet IDs (DB/cache)"
  value       = values(aws_subnet.private_data)[*].id
}
