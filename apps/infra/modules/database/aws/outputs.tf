output "db_host" { value = aws_db_instance.this.address }
output "db_port" { value = aws_db_instance.this.port }
output "db_name" { value = var.db_name }
output "db_user" { value = var.db_user }
output "db_password" {
  value     = random_password.db.result
  sensitive = true
}
output "db_dsn" {
  value     = "postgresql://${var.db_user}:${random_password.db.result}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${var.db_name}"
  sensitive = true
}
