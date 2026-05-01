terraform {
  backend "s3" {
    bucket         = "shopcloud-tfstate-prod-712044128773"
    key            = "infra/envs/prod/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "shopcloud-tf-locks-prod"
    encrypt        = true
  }
}
