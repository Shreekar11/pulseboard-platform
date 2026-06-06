output "cluster_name" { value = google_container_cluster.this.name }
output "cluster_endpoint" { value = google_container_cluster.this.endpoint }
output "cluster_ca" { value = try(google_container_cluster.this.master_auth[0].cluster_ca_certificate, "") }
output "kube_exec_auth" {
  value = "gcloud container clusters get-credentials ${google_container_cluster.this.name} --region ${var.region}"
}
output "workload_identity_ref" { value = "${var.project_id}.svc.id.goog" }
