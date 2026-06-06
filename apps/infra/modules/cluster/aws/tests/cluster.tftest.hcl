mock_provider "aws" {}

variables {
  name       = "pulseboard"
  region     = "us-east-1"
  network_id = "vpc-123"
  subnet_ids = ["subnet-a", "subnet-b"]
  node_count = 2
}

run "medium_maps_to_t3_medium" {
  command = plan

  # Stub out the EKS community module so mock_provider data-source
  # validation errors do not obscure the local.instance_type assertion.
  override_module {
    target = module.eks
    outputs = {
      cluster_name                       = "pulseboard"
      cluster_endpoint                   = "https://mock.eks.example.com"
      cluster_certificate_authority_data = "bW9jaw=="
      oidc_provider_arn                  = "arn:aws:iam::123456789012:oidc-provider/mock"
    }
  }

  variables {
    node_size = "medium"
  }

  assert {
    condition     = local.instance_type == "t3.medium"
    error_message = "node_size=medium must map to t3.medium"
  }
}

run "small_maps_to_t3_small" {
  command = plan

  override_module {
    target = module.eks
    outputs = {
      cluster_name                       = "pulseboard"
      cluster_endpoint                   = "https://mock.eks.example.com"
      cluster_certificate_authority_data = "bW9jaw=="
      oidc_provider_arn                  = "arn:aws:iam::123456789012:oidc-provider/mock"
    }
  }

  variables {
    node_size = "small"
  }

  assert {
    condition     = local.instance_type == "t3.small"
    error_message = "node_size=small must map to t3.small"
  }
}
