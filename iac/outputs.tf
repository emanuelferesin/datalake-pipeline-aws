output "bucket_name" {
  value = aws_s3_bucket.datalake.id
}

output "batch_role_arn" {
  value = aws_iam_role.batch_role.arn
}