mock_provider "google" {}

variables {
  name       = "pulseboard"
  region     = "us-central1"
  network_id = "projects/p/global/networks/n"
  subnet_ids = ["projects/p/regions/us-central1/subnetworks/s"]
  node_count = 2
}

run "medium_maps_to_e2_medium" {
  command = plan
  variables {
    node_size = "medium"
  }
  assert {
    condition     = local.machine_type == "e2-medium"
    error_message = "node_size=medium must map to e2-medium"
  }
}

run "small_maps_to_e2_small" {
  command = plan
  variables {
    node_size = "small"
  }
  assert {
    condition     = local.machine_type == "e2-small"
    error_message = "node_size=small must map to e2-small"
  }
}
