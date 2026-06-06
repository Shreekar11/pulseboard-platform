locals {
  machine_type = {
    small  = "e2-small"
    medium = "e2-medium"
    large  = "e2-standard-4"
  }[var.node_size]
}

resource "google_container_cluster" "this" {
  name       = var.name
  location   = var.region
  network    = var.network_id
  subnetwork = var.subnet_ids[0]

  remove_default_node_pool = true
  initial_node_count       = 1

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

resource "google_container_node_pool" "default" {
  name       = "default"
  location   = var.region
  cluster    = google_container_cluster.this.name
  node_count = var.node_count

  node_config {
    machine_type = local.machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}
