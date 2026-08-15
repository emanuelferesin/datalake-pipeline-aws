output "bucket_name" {
  value = aws_s3_bucket.datalake.id
}

output "batch_role_arn" {
  value = aws_iam_role.batch_role.arn
}

output "queue_url" {
  value = aws_sqs_queue.lotes_pendientes.url
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.batch.name
}