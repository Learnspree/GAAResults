terraform {
  backend "s3" {
    bucket = "tofustate-learnspree"
    key    = "gaaresults/tofustate"
    region = "us-east-1"
    profile = "default"
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "6.35.1"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
