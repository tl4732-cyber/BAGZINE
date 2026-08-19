# Container image registry for the Lambda scraper. Build & push the image
# (see ../../Dockerfile.lambda) before applying the Lambda function below.
resource "aws_ecr_repository" "scraper" {
  name                 = "${var.project_name}-scraper"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the repo small (ECR's free tier is 500 MB for the first 12 months) by
# pruning everything except the most recent few images.
resource "aws_ecr_lifecycle_policy" "scraper" {
  repository = aws_ecr_repository.scraper.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the 5 most recent images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = { type = "expire" }
      }
    ]
  })
}
