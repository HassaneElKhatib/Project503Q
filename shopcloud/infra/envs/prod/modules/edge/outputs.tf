output "zone_id" {
  value = aws_route53_zone.this.zone_id
}

output "name_servers" {
  value       = aws_route53_zone.this.name_servers
  description = "Delegate your domain or subdomain to these NS records"
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.cloudfront.arn
}

output "alb_acm_certificate_arn" {
  description = "ACM certificate ARN in the regional (EKS) account region for ALB HTTPS listeners"
  value       = aws_acm_certificate_validation.alb.certificate_arn
}
