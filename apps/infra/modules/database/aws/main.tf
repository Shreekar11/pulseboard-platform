locals {
  instance_class = {
    small  = "db.t3.small"
    medium = "db.t3.medium"
    large  = "db.r6g.large"
  }[var.db_size]
}

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "db" {
  name   = "${var.name}-db"
  vpc_id = var.network_id
  ingress {
    description = "postgres from within VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "this" {
  identifier             = var.name
  engine                 = "postgres"
  engine_version         = var.pg_version
  instance_class         = local.instance_class
  allocated_storage      = var.storage_gb
  db_name                = var.db_name
  username               = var.db_user
  password               = random_password.db.result
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  skip_final_snapshot    = true
  storage_encrypted      = true
}
