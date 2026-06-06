variable "name" { type = string }
variable "network_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "pg_version" {
  type    = string
  default = "16"
}
variable "db_size" {
  type    = string
  default = "small"
}
variable "storage_gb" {
  type    = number
  default = 20
}
variable "db_name" {
  type    = string
  default = "pulseboard"
}
variable "db_user" {
  type    = string
  default = "pulse"
}
