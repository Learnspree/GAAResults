resource "aws_s3_bucket" "frontend" {
  bucket = local.frontend_bucket_name

  tags = {
    Environment = local.environment
    Application = "gaa-results"
  }
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.frontend_bucket_name}-oac"
  description                       = "CloudFront access to the private GAA Results frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "frontend" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "api" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "api" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_function" "api_path_rewrite" {
  name    = "gaa-results-api-path-rewrite"
  runtime = "cloudfront-js-1.0"
  comment = "Remove the /api prefix before forwarding requests to API Gateway"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      if (request.uri === '/api') {
        request.uri = '/';
      } else if (request.uri.indexOf('/api/') === 0) {
        request.uri = request.uri.substring(4);
      }
      return request;
    }
  EOF
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  comment             = "GAA Results Angular frontend"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-${aws_s3_bucket.frontend.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    domain_name = "${aws_api_gateway_rest_api.gaa_results.id}.execute-api.${data.aws_region.current.region}.amazonaws.com"
    origin_id   = "api-${aws_api_gateway_rest_api.gaa_results.id}"
    origin_path = "/${aws_api_gateway_stage.gaa_results.stage_name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  ordered_cache_behavior {
    path_pattern             = "/api/*"
    target_origin_id         = "api-${aws_api_gateway_rest_api.gaa_results.id}"
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
    cache_policy_id          = data.aws_cloudfront_cache_policy.api.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.api.id

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.api_path_rewrite.arn
    }
  }

  default_cache_behavior {
    target_origin_id       = "s3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = data.aws_cloudfront_cache_policy.frontend.id

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Environment = local.environment
    Application = "gaa-results"
  }
}

data "aws_iam_policy_document" "frontend_cloudfront_access" {
  statement {
    sid    = "AllowCloudFrontReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_cloudfront_access.json

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

output "frontend_bucket_name" {
  description = "S3 bucket containing the private Angular frontend."
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_cloudfront_distribution_id" {
  description = "CloudFront distribution ID for frontend deployments."
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_cloudfront_domain_name" {
  description = "HTTPS CloudFront hostname for the Angular frontend."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "gaa_results_unified_api_url" {
  description = "API base URL through the unified CloudFront domain."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}/api"
}
