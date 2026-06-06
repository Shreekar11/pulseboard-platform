locals {
  instance_type = {
    small  = "t3.small"
    medium = "t3.medium"
    large  = "m6i.large"
  }[var.node_size]
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.name
  cluster_version = var.k8s_version

  vpc_id     = var.network_id
  subnet_ids = var.subnet_ids

  cluster_endpoint_public_access = true
  enable_irsa                    = true

  eks_managed_node_groups = {
    default = {
      instance_types = [local.instance_type]
      min_size       = 1
      max_size       = var.node_count + 2
      desired_size   = var.node_count
    }
  }
}
