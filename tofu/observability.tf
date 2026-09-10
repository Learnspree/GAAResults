resource "aws_cloudwatch_log_group" "frontend_access" {
  name              = "/aws/cloudfront/gaa-results"
  retention_in_days = 180

  tags = {
    Environment = local.environment
    Application = "gaa-results"
  }
}

data "aws_iam_policy_document" "frontend_access_logs" {
  statement {
    sid    = "AllowCloudFrontAccessLogDelivery"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutLogEventsBatch"
    ]

    resources = ["${aws_cloudwatch_log_group.frontend_access.arn}:*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_cloudwatch_log_resource_policy" "frontend_access" {
  policy_document = data.aws_iam_policy_document.frontend_access_logs.json
  policy_name     = "gaa-results-cloudfront-access-logs"
}

resource "aws_cloudwatch_log_delivery_source" "frontend_access" {
  name         = "gaa-results-cloudfront-access"
  log_type     = "ACCESS_LOGS"
  resource_arn = aws_cloudfront_distribution.frontend.arn
}

resource "aws_cloudwatch_log_delivery_destination" "frontend_access" {
  name          = "gaa-results-cloudfront-access"
  output_format = "json"

  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.frontend_access.arn
  }
}

resource "aws_cloudwatch_log_delivery" "frontend_access" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.frontend_access.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.frontend_access.arn

  record_fields = [
    "date",
    "time",
    "x-edge-location",
    "c-ip",
    "cs-method",
    "cs-uri-stem",
    "sc-status",
    "cs(Referer)",
    "cs(User-Agent)",
    "x-edge-result-type"
  ]

  depends_on = [aws_cloudwatch_log_resource_policy.frontend_access]
}

resource "aws_cloudwatch_dashboard" "frontend" {
  dashboard_name = "gaa-results-frontend"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Requests"
          region = "us-east-1"
          view   = "timeSeries"
          stat    = "Sum"
          period = 300
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.frontend.id, "Region", "Global"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "HTTP errors"
          region = "us-east-1"
          view   = "timeSeries"
          stat   = "Average"
          period = 300
          metrics = [
            ["AWS/CloudFront", "4xxErrorRate", "DistributionId", aws_cloudfront_distribution.frontend.id, "Region", "Global"],
            ["AWS/CloudFront", "5xxErrorRate", "DistributionId", aws_cloudfront_distribution.frontend.id, "Region", "Global"]
          ]
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 8
        properties = {
          title  = "Recent page requests"
          region = "us-east-1"
          query  = "SOURCE '${aws_cloudwatch_log_group.frontend_access.name}' | fields @timestamp, `cs-uri-stem`, `sc-status`, `cs(User-Agent)` | sort @timestamp desc | limit 100"
          view   = "table"
        }
      }
    ]
  })
}

output "frontend_access_log_group_name" {
  description = "CloudWatch Logs group retaining CloudFront access logs for 180 days."
  value       = aws_cloudwatch_log_group.frontend_access.name
}

output "frontend_dashboard_name" {
  description = "CloudWatch dashboard for frontend traffic and access logs."
  value       = aws_cloudwatch_dashboard.frontend.dashboard_name
}
