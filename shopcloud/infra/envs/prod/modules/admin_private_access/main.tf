resource "aws_route53_zone" "private_split" {
  name = var.domain_name

  vpc {
    vpc_id = var.vpc_id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-split-${var.domain_name}"
  })
}

data "aws_lb" "admin_internal" {
  tags = {
    "ingress.k8s.aws/stack" = "shopcloud-admin"
    "elbv2.k8s.aws/cluster" = var.cluster_name
  }
}

resource "aws_route53_record" "admin_alias" {
  zone_id = aws_route53_zone.private_split.zone_id
  name    = var.record_label
  type    = "A"

  alias {
    name                   = data.aws_lb.admin_internal.dns_name
    zone_id                = data.aws_lb.admin_internal.zone_id
    evaluate_target_health = true
  }
}

locals {
  admin_fqdn = "${var.record_label}.${var.domain_name}"
}

resource "aws_acm_certificate" "admin_https" {
  domain_name       = local.admin_fqdn
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = var.tags
}

resource "aws_route53_record" "admin_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.admin_https.domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id         = var.public_zone_id
  name            = each.value.name
  type            = each.value.type
  ttl             = 60
  records         = [each.value.record]
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "admin_https" {
  certificate_arn         = aws_acm_certificate.admin_https.arn
  validation_record_fqdns = [for r in aws_route53_record.admin_cert_validation : r.fqdn]

  timeouts {
    create = "45m"
  }
}
