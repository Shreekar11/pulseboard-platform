variable "name" {
  type    = string
  default = "pulseboard"
}
variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "node_count" {
  type    = number
  default = 2
}
variable "node_size" {
  type    = string
  default = "medium"
}
variable "db_size" {
  type    = string
  default = "small"
}
