# Email alert when a scheduled crawl run fails. After `terraform apply`, AWS
# emails var.alert_email a confirmation link -- alerts won't deliver until
# it's clicked (this step can't be automated by Terraform).
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-scraper-alerts"
}

resource "aws_sns_topic_subscription" "alert_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "scraper_errors" {
  alarm_name          = "${var.project_name}-scraper-errors"
  alarm_description   = "Fires when the ${var.project_name}-scraper Lambda raises an error"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions = {
    FunctionName = aws_lambda_function.scraper.function_name
  }
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}
