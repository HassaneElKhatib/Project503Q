variable "cluster_name" {
  type = string
}

variable "cluster_endpoint" {
  type = string
}

variable "cluster_ca_data" {
  type      = string
  sensitive = true
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "alb_controller_role_arn" {
  type = string
}

variable "cluster_autoscaler_role_arn" {
  type = string
}

variable "external_secrets_role_arn" {
  type = string
}

variable "aws_lb_controller_chart_version" {
  type    = string
  default = "1.8.1"
}

variable "external_secrets_chart_version" {
  type    = string
  default = "0.10.7"
}

variable "metrics_server_chart_version" {
  type    = string
  default = "3.12.1"
}

variable "cluster_autoscaler_chart_version" {
  type    = string
  default = "9.37.0"
}
