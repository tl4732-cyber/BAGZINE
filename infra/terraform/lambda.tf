# Created explicitly (rather than left to Lambda's implicit auto-creation)
# so retention is bounded -- otherwise CloudWatch Logs keeps everything
# forever, which slowly costs money outside the free tier.
resource "aws_cloudwatch_log_group" "scraper" {
  name              = "/aws/lambda/${var.project_name}-scraper"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "scraper" {
  function_name = "${var.project_name}-scraper"
  role          = aws_iam_role.scraper_lambda.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.scraper.repository_url}:${var.lambda_image_tag}"

  timeout     = var.lambda_timeout_seconds
  memory_size = var.lambda_memory_mb

  environment {
    variables = {
      S3_ARCHIVE_BUCKET  = aws_s3_bucket.raw_listings.bucket
      S3_ARCHIVE_PREFIX  = var.s3_archive_prefix
      EBAY_CLIENT_ID     = var.ebay_client_id
      EBAY_CLIENT_SECRET = var.ebay_client_secret
      EBAY_ENV           = var.ebay_env
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.scraper,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_s3_write,
  ]
}
