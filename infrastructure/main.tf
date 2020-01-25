/* Bucket for storing deployment state */
terraform {
  backend "s3" {
    bucket = "drongo-gpx-terraform-state"
    key    = "terraform-state"
    region = "eu-west-1"
    profile = "benwindsor"
  }
}

provider "aws" {
    profile = var.profile
    region = var.aws_region
}


locals {
  deployment_name = "tf-drongo-gpx"
}
