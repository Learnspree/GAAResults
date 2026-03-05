terraform {
  backend "s3" {
    bucket = "tofustate-learnspree"
    key    = "gaaresults/tofustate"
    region = "us-east-1"
  }
}
