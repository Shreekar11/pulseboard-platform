terraform {
  backend "gcs" {
    bucket = "pulseboard-tfstate"
    prefix = "gcp"
  }
}
