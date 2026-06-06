output "cluster_auth" { value = module.cluster.kube_exec_auth }
output "registry_url" { value = module.registry.registry_url }
output "db_dsn" {
  value     = module.database.db_dsn
  sensitive = true
}
