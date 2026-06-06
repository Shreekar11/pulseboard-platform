mock_provider "google" {}

variables {
  name       = "pulseboard"
  region     = "us-central1"
  network_id = "projects/p/global/networks/n"
  pg_version = "POSTGRES_16"
}

run "medium_maps_to_custom_tier" {
  command = plan
  variables {
    db_size = "medium"
  }
  assert {
    condition     = google_sql_database_instance.this.settings[0].tier == "db-custom-2-7680"
    error_message = "db_size=medium must map to db-custom-2-7680"
  }
  assert {
    condition     = google_sql_database_instance.this.settings[0].ip_configuration[0].ipv4_enabled == false
    error_message = "Cloud SQL must not expose a public IPv4"
  }
}

run "small_maps_to_micro" {
  command = plan
  variables {
    db_size = "small"
  }
  assert {
    condition     = google_sql_database_instance.this.settings[0].tier == "db-f1-micro"
    error_message = "db_size=small must map to db-f1-micro"
  }
}
