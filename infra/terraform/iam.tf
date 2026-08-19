data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scraper_lambda" {
  name               = "${var.project_name}-scraper-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# CloudWatch Logs (CreateLogGroup/Stream, PutLogEvents) for the function.
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.scraper_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Least-privilege: only allow writing objects under the archive prefix in
# this one bucket -- no read/delete/list, and no access to any other bucket.
data "aws_iam_policy_document" "lambda_s3_write" {
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.raw_listings.arn}/${var.s3_archive_prefix}/*"]
  }
}

resource "aws_iam_role_policy" "lambda_s3_write" {
  name   = "${var.project_name}-scraper-s3-write"
  role   = aws_iam_role.scraper_lambda.id
  policy = data.aws_iam_policy_document.lambda_s3_write.json
}
