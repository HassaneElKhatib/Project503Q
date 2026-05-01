variable "aws_region" {
  description = "Region where the Terraform state bucket and lock table live."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  type    = string
  default = "shopcloud"
}

variable "force_destroy" {
  description = "Allow destroying the state bucket without emptying it (only set true for throwaway accounts)."
  type        = bool
  default     = false
}
