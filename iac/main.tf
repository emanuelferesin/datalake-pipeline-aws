resource "aws_iam_role" "batch_role" {
  name               = "batch-role"
  assume_role_policy = file("${path.module}/../iam/trust_policy.json")
}

resource "aws_iam_role_policy" "batch_role_s3" {
  name   = "BatchRoleS3Access"
  role   = aws_iam_role.batch_role.id
  policy = file("${path.module}/../iam/batch_role_policy.json")
}

resource "aws_s3_bucket" "datalake" {
  bucket = "datalake-ventas"
}

resource "aws_s3_bucket_public_access_block" "datalake" {
  bucket                  = aws_s3_bucket.datalake.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  policy = file("${path.module}/../s3/bucket_policy.json")

  depends_on = [aws_iam_role.batch_role]
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "datalake-vpc" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"

  tags = { Name = "private-1b", Tier = "private" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "rt-private" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = { Name = "vpce-s3" }
}

resource "aws_security_group" "app_private" {
  name        = "app-private-sg"
  description = "Batch job en subred privada"
  vpc_id      = aws_vpc.main.id

  egress {
    description     = "HTTPS a S3 via VPC endpoint"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    prefix_list_ids = [aws_vpc_endpoint.s3.prefix_list_id]
  }

  tags = { Name = "app-private-sg" }
}

resource "aws_iam_instance_profile" "batch" {
  name = "batch-instance-profile"
  role = aws_iam_role.batch_role.name
}

resource "aws_instance" "batch" {
  ami                    = "ami-0c02fb55956c7d316"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.private.id
  vpc_security_group_ids = [aws_security_group.app_private.id]
  iam_instance_profile   = aws_iam_instance_profile.batch.name

  user_data = <<-EOF
    #!/bin/bash
    # En AWS real esto instalaria dependencias y correria el batch job.
    # La logica real vive en scripts/procesar_lote.py (se corre aparte,
    # ver ADR: LocalStack Community no ejecuta user-data ni Auto Scaling).
    echo "batch job placeholder"
  EOF

  tags = { Name = "datalake-batch", Role = "batch-processing" }
}

resource "aws_secretsmanager_secret" "db" {
  name        = "app/db"
  description = "Credencial de la base curated"
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = "app"
    password = var.db_password
    dbname   = "appdb"
    host     = "localhost"
    port     = 5432
  })
}

resource "aws_sqs_queue" "lotes_pendientes" {
  name                       = "datalake-lotes-pendientes"
  visibility_timeout_seconds = 60
}

resource "aws_cloudwatch_log_group" "batch" {
  name              = "/datalake/batch"
  retention_in_days = 14
}