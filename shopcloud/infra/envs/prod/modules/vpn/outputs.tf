output "client_vpn_endpoint_id" {
  value = aws_ec2_client_vpn_endpoint.this.id
}

output "client_vpn_dns_name" {
  value = aws_ec2_client_vpn_endpoint.this.dns_name
}

output "client_vpn_security_group_id" {
  value = aws_security_group.client_vpn.id
}

output "client_vpn_client_cidr" {
  value = aws_ec2_client_vpn_endpoint.this.client_cidr_block
}

output "client_vpn_saml_provider_arn" {
  description = "IAM SAML provider ARN used for federated VPN auth (null if disabled)."
  value       = local.resolved_saml_arn
}
