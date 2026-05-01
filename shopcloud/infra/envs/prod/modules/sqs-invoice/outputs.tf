output "invoice_queue_url" {
  description = "Invoice queue URL."
  value       = aws_sqs_queue.main.url
}

output "invoice_queue_arn" {
  description = "Invoice queue ARN for checkout IRSA policy."
  value       = aws_sqs_queue.main.arn
}

output "invoices_bucket_name" {
  description = "Invoices S3 bucket name."
  value       = aws_s3_bucket.invoices.bucket
}

output "secret_arn_invoice_queue" {
  description = "Secrets Manager ARN containing invoice queue URL."
  value       = aws_secretsmanager_secret.invoice_queue.arn
}
