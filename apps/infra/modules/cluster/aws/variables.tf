variable "name" { type = string }
variable "region" { type = string }
variable "network_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "node_count" {
  type    = number
  default = 2
}
variable "node_size" {
  type    = string
  default = "medium"
}
variable "k8s_version" {
  type    = string
  default = "1.30"
}
