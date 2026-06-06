mock_provider "aws" {}

variables {
  name       = "pulseboard"
  network_id = "vpc-123"
  subnet_ids = ["subnet-a", "subnet-b"]
  pg_version = "16"
  storage_gb = 20
}

run "medium_maps_to_db_t3_medium" {
  command = plan
  variables {
    db_size = "medium"
  }
  assert {
    condition     = aws_db_instance.this.instance_class == "db.t3.medium"
    error_message = "db_size=medium must map to db.t3.medium"
  }
  assert {
    condition     = aws_db_instance.this.publicly_accessible == false
    error_message = "managed Postgres must never be publicly accessible"
  }
}

run "small_maps_to_db_t3_small" {
  command = plan
  variables {
    db_size = "small"
  }
  assert {
    condition     = aws_db_instance.this.instance_class == "db.t3.small"
    error_message = "db_size=small must map to db.t3.small"
  }
}
