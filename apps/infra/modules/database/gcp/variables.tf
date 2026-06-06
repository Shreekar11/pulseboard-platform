variable "name" { type = string }
variable "region" { type = string }
variable "network_id" { type = string }
variable "pg_version" {
  type    = string
  default = "POSTGRES_16"
}
variable "db_size" {
  type    = string
  default = "small"
}
variable "db_name" {
  type    = string
  default = "pulseboard"
}
variable "db_user" {
  type    = string
  default = "pulse"
}
