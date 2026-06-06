module "network" {
  source = "../../modules/network/gcp"
  name   = var.name
  region = var.region
}

module "registry" {
  source     = "../../modules/registry/gcp"
  name       = var.name
  region     = var.region
  project_id = var.project_id
}

module "database" {
  source     = "../../modules/database/gcp"
  name       = var.name
  region     = var.region
  network_id = module.network.network_id
  db_size    = var.db_size
}

module "cluster" {
  source     = "../../modules/cluster/gcp"
  name       = var.name
  region     = var.region
  network_id = module.network.network_id
  subnet_ids = module.network.private_subnet_ids
  node_count = var.node_count
  node_size  = var.node_size
  project_id = var.project_id
}
