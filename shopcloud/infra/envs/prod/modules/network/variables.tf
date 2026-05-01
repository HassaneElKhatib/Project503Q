variable "name_prefix" {
  description = "Resource name prefix, for example shopcloud-prod"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "azs" {
  description = "Availability zones used by the VPC"
  type        = list(string)

  validation {
    condition     = length(var.azs) == 2
    error_message = "This module expects exactly 2 AZs (6 subnets: public/app/data across 2 AZs)."
  }
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs (one per AZ)"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidrs) == length(var.azs)
    error_message = "public_subnet_cidrs must provide one CIDR per AZ."
  }
}

variable "private_app_subnet_cidrs" {
  description = "Private application subnet CIDRs (one per AZ)"
  type        = list(string)

  validation {
    condition     = length(var.private_app_subnet_cidrs) == length(var.azs)
    error_message = "private_app_subnet_cidrs must provide one CIDR per AZ."
  }
}

variable "private_data_subnet_cidrs" {
  description = "Private data subnet CIDRs (one per AZ)"
  type        = list(string)

  validation {
    condition     = length(var.private_data_subnet_cidrs) == length(var.azs)
    error_message = "private_data_subnet_cidrs must provide one CIDR per AZ."
  }
}

variable "nat_gateway_count" {
  description = "NAT gateways to create (1 dev, 2 prod)"
  type        = number
  default     = 1

  validation {
    condition     = var.nat_gateway_count >= 1 && var.nat_gateway_count <= length(var.azs)
    error_message = "nat_gateway_count must be between 1 and the AZ count."
  }
}
