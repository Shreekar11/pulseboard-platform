module "network" {
  source = "../../modules/network/aws"
  name   = var.name
}

module "registry" {
  source = "../../modules/registry/aws"
  name   = var.name
}

module "database" {
  source     = "../../modules/database/aws"
  name       = var.name
  network_id = module.network.network_id
  subnet_ids = module.network.private_subnet_ids
  db_size    = var.db_size
}

module "cluster" {
  source     = "../../modules/cluster/aws"
  name       = var.name
  region     = var.region
  network_id = module.network.network_id
  subnet_ids = module.network.private_subnet_ids
  node_count = var.node_count
  node_size  = var.node_size
}
