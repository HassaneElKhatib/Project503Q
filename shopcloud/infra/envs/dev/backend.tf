terraform {
  backend "s3" {
    bucket         = "shopcloud-tfstate-712044128773"
    key            = "infra/envs/dev/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "shopcloud-tf-locks"
    encrypt        = true
  }
}
