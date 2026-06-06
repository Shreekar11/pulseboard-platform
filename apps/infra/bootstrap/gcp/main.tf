terraform {
  required_version = ">= 1.7"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "state" {
  name                        = var.state_bucket
  location                    = var.region
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}
