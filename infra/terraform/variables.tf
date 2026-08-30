variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for every resource (bucket, ECR repo, Lambda, etc.)."
  type        = string
  default     = "bagzine"
}

variable "alert_email" {
  description = "Email address that receives SNS alerts when a scheduled crawl fails. AWS will send a confirmation link to this address after `terraform apply` -- you must click it once for alerts to start delivering."
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule for the daily crawl (cron in UTC). Default: 09:00 UTC daily."
  type        = string
  default     = "cron(0 9 * * ? *)"
}

variable "s3_archive_prefix" {
  description = "Key prefix under the raw-listings bucket that the Lambda scraper writes to."
  type        = string
  default     = "raw"
}

variable "raw_object_expiration_days" {
  description = "Days to keep raw archived listings in S3 before they expire. Set to 0 to disable expiration."
  type        = number
  default     = 180
}

variable "lambda_image_tag" {
  description = "Image tag in the ECR repo to deploy. Push an image with this tag before the first `terraform apply` that creates the Lambda function (see infra/terraform/README.md)."
  type        = string
  default     = "latest"
}

variable "lambda_memory_mb" {
  description = "Lambda memory allocation in MB. Also proportionally scales CPU."
  type        = number
  default     = 1024
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds. The daily crawl runs ~16 eBay queries sequentially plus Fashionphile, so this is set high; increase further if jobs start timing out."
  type        = number
  default     = 900
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the Lambda function's log group."
  type        = number
  default     = 14
}

variable "ebay_client_id" {
  description = "eBay Browse API client ID. Leave blank to run the Lambda crawler in mock mode (writes 2 sample eBay items instead of calling the real API)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "ebay_client_secret" {
  description = "eBay Browse API client secret. Leave blank to run the Lambda crawler in mock mode."
  type        = string
  default     = ""
  sensitive   = true
}

variable "ebay_env" {
  description = "eBay API environment: \"sandbox\" or \"production\"."
  type        = string
  default     = "sandbox"
}

variable "monthly_budget_usd" {
  description = "Email alert threshold if AWS bills this account more than this amount in a month. At this project's volume, everything should stay in the Free Tier (i.e. $0) -- this is a tripwire, not an expected cost."
  type        = number
  default     = 2
}
