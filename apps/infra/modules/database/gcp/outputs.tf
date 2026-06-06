output "db_host" { value = google_sql_database_instance.this.private_ip_address }
output "db_port" { value = 5432 }
output "db_name" { value = var.db_name }
output "db_user" { value = var.db_user }
output "db_password" {
  value     = random_password.db.result
  sensitive = true
}
output "db_dsn" {
  value     = "postgresql://${var.db_user}:${random_password.db.result}@${google_sql_database_instance.this.private_ip_address}:5432/${var.db_name}"
  sensitive = true
}
