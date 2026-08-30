# Terraform: automated scraping pipeline on AWS

Provisions the AWS side of **Tier 2** (see the root [README](../../README.md#aws-pipeline-tier-2)):

```
EventBridge (cron) --> Lambda (Scrapy: ebay_api + fashionphile) --> S3 (raw/bronze landing zone)
                                                                          |
                                                    scripts/load_from_s3.py (run locally, or from
                                                    any host that can reach your Postgres instance)
                                                                          |
                                                                     Postgres
```

Resources created: S3 bucket, ECR repo, IAM role/policy, Lambda function, CloudWatch Log Group,
an EventBridge rule + target, an SNS topic + CloudWatch alarm for failure alerts, and an AWS
Budget cost tripwire.

Everything here fits in the AWS Free Tier for a low-volume daily job (see cost notes in the root
README). Nothing here touches or requires Postgres/RDS — the Lambda function never talks to your
database, by design (see `scrapers/bags/settings_lambda.py`).

## Cost & safety

At this project's volume, expected AWS cost is **$0/month**:

| Service | Free tier | This project's usage |
|---|---|---|
| Lambda | 1M requests + 400,000 GB-seconds/month, forever | ~30 invocations/month, ~27,000 GB-seconds at worst (1024 MB × 900s) |
| S3 | 5 GB storage (12 months, new accounts) | A few MB of JSON, expires after `raw_object_expiration_days` (default 180) |
| ECR | 500 MB (12 months, new accounts) | One image, ~150–300 MB, pruned to the 5 most recent by lifecycle policy |
| EventBridge / CloudWatch Logs (5 GB) / 10 alarms / SNS (1,000 emails) | Free, forever | Negligible at one run/day |

Two things to know:

- **AWS requires a credit card to create an account**, even to use the Free Tier — this doesn't
  mean you'll be charged, but it's unavoidable.
- **`terraform apply` also creates an [AWS Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)**
  (`budget.tf`) that emails `alert_email` if actual or forecasted spend crosses `monthly_budget_usd`
  (default $2) — a tripwire in case something outside this design starts costing money, not an
  expected cost. AWS Budgets doesn't charge for your account's first two budgets, so this is free
  too. Also worth turning on **Billing preferences → "Receive Free Tier Usage Alerts"** in the AWS
  console (separate from this Terraform, and it emails the account's root address).
- Run `terraform destroy` (see below) when you're done demoing/using this, since idle-but-not-torn-down
  resources are the most common way side projects rack up surprise charges over time.

## Prerequisites

- An AWS account and the AWS CLI configured (`aws configure`) with credentials that can create
  IAM/S3/ECR/Lambda/EventBridge/SNS/CloudWatch resources.
- Docker, to build the Lambda container image.
- Terraform >= 1.5.

## Deploy (two-phase, because Lambda needs an image to already exist in ECR)

**1. Create the ECR repo first** (and everything else that doesn't depend on the image):

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # fill in alert_email at minimum
terraform init
terraform apply -target=aws_ecr_repository.scraper
```

**2. Build and push the image:**

```bash
cd ../..   # project root
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1   # match var.aws_region

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

docker build -f Dockerfile.lambda -t bagzine-scraper .
docker tag bagzine-scraper:latest "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/bagzine-scraper:latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/bagzine-scraper:latest"
```

**3. Apply everything else** (Lambda, EventBridge schedule, SNS, alarms):

```bash
cd infra/terraform
terraform apply
```

Confirm the SNS email subscription AWS sends to `alert_email` — alerts won't deliver until you
click the link.

## Test it

```bash
aws lambda invoke --function-name bagzine-scraper --payload '{}' --cli-binary-format raw-in-base64-out /tmp/out.json
cat /tmp/out.json
aws s3 ls "s3://$(terraform output -raw s3_bucket_name)/raw/" --recursive
```

Then load whatever landed in S3 into your local Postgres:

```bash
cd ../..
export S3_ARCHIVE_BUCKET=$(cd infra/terraform && terraform output -raw s3_bucket_name)
python3 scripts/load_from_s3.py
```

## Updating the image later

Re-run the `docker build`/`tag`/`push` steps from phase 2 with a new tag (or `:latest` again), then:

```bash
terraform apply -replace=aws_lambda_function.scraper
```

## Tear down

```bash
terraform destroy
```

S3 objects are not automatically emptied when a bucket is destroyed — if the bucket has objects in
it, either delete them first (`aws s3 rm s3://<bucket> --recursive`) or `terraform destroy` will
fail on that resource.
