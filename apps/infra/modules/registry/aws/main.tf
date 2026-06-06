resource "aws_ecr_repository" "this" {
  for_each             = toset(var.repositories)
  name                 = "${var.name}/${each.value}"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

# All repos share one registry host; expose that host as the prefix.
locals {
  registry_url = split("/", values(aws_ecr_repository.this)[0].repository_url)[0]
}
