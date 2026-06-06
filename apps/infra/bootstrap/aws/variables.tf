variable "region" {
  type    = string
  default = "us-east-1"
}

variable "state_bucket" {
  type    = string
  default = "pulseboard-tfstate"
}

variable "lock_table" {
  type    = string
  default = "pulseboard-tflock"
}
