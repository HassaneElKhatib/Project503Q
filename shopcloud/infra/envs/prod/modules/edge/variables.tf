variable "name_prefix" { type = string }
variable "domain_name" { type = string }
variable "origin_domain_name" { type = string }
variable "waf_scope" {
  type    = string
  default = "CLOUDFRONT"
}
