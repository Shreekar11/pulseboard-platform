locals {
  tier = {
    small  = "db-f1-micro"
    medium = "db-custom-2-7680"
    large  = "db-custom-4-15360"
  }[var.db_size]
}

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "this" {
  name             = var.name
  region           = var.region
  database_version = var.pg_version

  settings {
    tier = local.tier
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "this" {
  name     = var.db_name
  instance = google_sql_database_instance.this.name
}

resource "google_sql_user" "this" {
  name     = var.db_user
  instance = google_sql_database_instance.this.name
  password = random_password.db.result
}
