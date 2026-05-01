variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "association_subnet_ids" {
  type = list(string)
}

variable "server_certificate_arn" {
  type = string
}

variable "client_root_certificate_chain_arn" {
  type = string
}

variable "client_cidr_block" {
  type = string
}

variable "split_tunnel" {
  type    = bool
  default = true
}

variable "saml_provider_arn" {
  type    = string
  default = null
}

variable "self_service_saml_provider_arn" {
  type    = string
  default = null
}

variable "enable_federated_authentication" {
  description = "Add SAML federated authentication (use IdP MFA). Requires saml_provider_arn or saml_metadata_document."
  type        = bool
  default     = false

  validation {
    condition = !var.enable_federated_authentication || var.saml_provider_arn != null || (
      try(length(trimspace(coalesce(var.saml_metadata_document, ""))), 0) > 0
    )
    error_message = "When enable_federated_authentication is true, set either saml_provider_arn or a non-empty saml_metadata_document (IdP metadata XML)."
  }
}

variable "saml_metadata_document" {
  description = "IdP SAML metadata XML body; creates aws_iam_saml_provider when enable_federated_authentication is true and saml_provider_arn is null."
  type        = string
  default     = null
  sensitive   = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
