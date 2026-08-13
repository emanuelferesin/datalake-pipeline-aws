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