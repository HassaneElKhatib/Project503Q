locals {
  create_iam_saml_provider = var.enable_federated_authentication && var.saml_provider_arn == null && var.saml_metadata_document != null
  resolved_saml_arn = var.enable_federated_authentication ? (
    var.saml_provider_arn != null ? var.saml_provider_arn : try(aws_iam_saml_provider.client_vpn[0].arn, null)
  ) : null
}

resource "aws_iam_saml_provider" "client_vpn" {
  count                  = local.create_iam_saml_provider ? 1 : 0
  name                   = "${var.name_prefix}-client-vpn-saml"
  saml_metadata_document = var.saml_metadata_document
}

resource "aws_security_group" "client_vpn" {
  name        = "${var.name_prefix}-client-vpn"
  description = "Client VPN endpoint security group"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }
}

resource "aws_ec2_client_vpn_endpoint" "this" {
  description            = "${var.name_prefix} admin client vpn"
  server_certificate_arn = var.server_certificate_arn
  client_cidr_block      = var.client_cidr_block
  split_tunnel           = var.split_tunnel
  vpc_id                 = var.vpc_id
  security_group_ids     = [aws_security_group.client_vpn.id]
  transport_protocol     = "udp"
  vpn_port               = 443

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = var.client_root_certificate_chain_arn
  }

  dynamic "authentication_options" {
    for_each = local.resolved_saml_arn != null ? [local.resolved_saml_arn] : []
    content {
      type                           = "federated-authentication"
      saml_provider_arn              = authentication_options.value
      self_service_saml_provider_arn = var.self_service_saml_provider_arn
    }
  }

  connection_log_options {
    enabled = false
  }

  lifecycle {
    precondition {
      condition = !var.enable_federated_authentication || var.saml_provider_arn != null || (
        try(length(trimspace(coalesce(var.saml_metadata_document, ""))), 0) > 0
      )
      error_message = "When enable_federated_authentication is true, set either saml_provider_arn or a non-empty saml_metadata_document (IdP metadata XML)."
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-client-vpn"
  })
}

resource "aws_ec2_client_vpn_network_association" "this" {
  for_each = toset(var.association_subnet_ids)

  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.this.id
  subnet_id              = each.value
}

resource "aws_ec2_client_vpn_authorization_rule" "vpc" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.this.id
  target_network_cidr    = var.vpc_cidr
  authorize_all_groups   = true
}
