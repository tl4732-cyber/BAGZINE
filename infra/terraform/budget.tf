# Cost tripwire, not an expected cost: at this project's volume (Lambda's
# always-free 1M requests/400K GB-seconds per month covers ~30 invocations
# easily; S3/ECR storage is a few MB), everything should stay at $0. This
# alerts var.alert_email if that ever stops being true. AWS Budgets does not
# charge for the first two budgets per account, so this resource is itself
# free.
resource "aws_budgets_budget" "cost_guard" {
  name         = "${var.project_name}-monthly-cost-guard"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
