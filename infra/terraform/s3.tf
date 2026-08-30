# Raw/bronze landing zone for scraped listings. The Lambda scraper (S3RawArchivePipeline)
# writes newline-delimited JSON here; scripts/load_from_s3.py reads it from a machine
# that can reach Postgres and replays it through the normal matching/upsert pipeline.
resource "aws_s3_bucket" "raw_listings" {
  bucket = "${var.project_name}-raw-listings-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "raw_listings" {
  bucket = aws_s3_bucket.raw_listings.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_listings" {
  bucket = aws_s3_bucket.raw_listings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_listings" {
  count  = var.raw_object_expiration_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.raw_listings.id

  rule {
    id     = "expire-raw-archives"
    status = "Enabled"

    filter {
      prefix = "${var.s3_archive_prefix}/"
    }

    expiration {
      days = var.raw_object_expiration_days
    }
  }
}
