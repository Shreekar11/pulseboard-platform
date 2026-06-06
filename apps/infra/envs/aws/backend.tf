terraform {
  backend "s3" {
    bucket         = "pulseboard-tfstate"
    key            = "aws/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "pulseboard-tflock"
    encrypt        = true
  }
}
