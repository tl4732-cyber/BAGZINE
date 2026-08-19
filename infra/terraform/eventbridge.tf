# Replaces the local cron/`scripts/crawl_daily.sh` schedule with a managed
# EventBridge rule -- same cadence, but runs even when your machine is off.
resource "aws_cloudwatch_event_rule" "daily_crawl" {
  name                = "${var.project_name}-daily-crawl"
  description         = "Triggers the ${var.project_name}-scraper Lambda on a schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "daily_crawl" {
  rule = aws_cloudwatch_event_rule.daily_crawl.name
  arn  = aws_lambda_function.scraper.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scraper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_crawl.arn
}
