variable "name_prefix" {
  type = string
}

variable "domain_name" {
  description = "Public Route53 zone name (same as associated private zone name)."
  type        = string
}

variable "vpc_id" {
  type = string
}

variable "public_zone_id" {
  description = "Public hosted zone ID (ACM DNS validation records)."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "record_label" {
  description = "Relative record in the zone (e.g. priv-admin -> priv-admin.<domain_name>)."
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
