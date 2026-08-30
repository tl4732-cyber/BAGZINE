output "ecr_repository_url" {
  description = "Push the Lambda image here before the first full `terraform apply`."
  value       = aws_ecr_repository.scraper.repository_url
}

output "s3_bucket_name" {
  description = "Raw-listings landing zone. Pass this to scripts/load_from_s3.py as S3_ARCHIVE_BUCKET."
  value       = aws_s3_bucket.raw_listings.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.scraper.function_name
}

output "sns_topic_arn" {
  description = "Confirm the subscription email sent to var.alert_email to start receiving failure alerts."
  value       = aws_sns_topic.alerts.arn
}

output "eventbridge_schedule" {
  value = aws_cloudwatch_event_rule.daily_crawl.schedule_expression
}

output "monthly_budget_usd" {
  description = "You'll get an email at var.alert_email if actual/forecasted spend crosses this."
  value       = var.monthly_budget_usd
}
