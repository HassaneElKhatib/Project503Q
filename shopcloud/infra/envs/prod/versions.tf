terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 5.50.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "= 3.6.2"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "= 2.13.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "= 2.30.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "= 4.0.5"
    }
  }
}
