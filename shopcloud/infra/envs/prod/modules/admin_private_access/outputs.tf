output "admin_fqdn" {
  description = "Private admin FQDN."
  value       = local.admin_fqdn
}

output "admin_certificate_arn" {
  description = "Regional ACM ARN for admin ALB HTTPS."
  value       = aws_acm_certificate_validation.admin_https.certificate_arn
}

output "private_zone_id" {
  value = aws_route53_zone.private_split.zone_id
}
