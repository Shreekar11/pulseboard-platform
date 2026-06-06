variable "name" { type = string }
variable "region" { type = string }
variable "cidr" {
  type    = string
  default = "10.10.0.0/16"
}
