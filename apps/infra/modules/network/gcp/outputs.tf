output "network_id" { value = google_compute_network.this.id }
output "private_subnet_ids" { value = [google_compute_subnetwork.private.id] }
output "public_subnet_ids" { value = [] }
