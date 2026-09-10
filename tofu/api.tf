resource "aws_api_gateway_rest_api" "gaa_results" {
  name        = "gaa-results-api-${local.environment}"
  description = "GAA Results API"
  body        = file("${path.module}/api/openapi.yaml")

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  api_key_source = "HEADER"
}

resource "aws_api_gateway_deployment" "gaa_results" {
  rest_api_id = aws_api_gateway_rest_api.gaa_results.id

  triggers = {
    openapi = sha256(file("${path.module}/api/openapi.yaml"))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "gaa_results" {
  rest_api_id   = aws_api_gateway_rest_api.gaa_results.id
  deployment_id = aws_api_gateway_deployment.gaa_results.id
  stage_name    = local.environment
}

resource "aws_api_gateway_api_key" "gaa_results" {
  name    = "gaa-results-api-key-${local.environment}"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "gaa_results" {
  name        = "gaa-results-api-plan-${local.environment}"
  description = "Usage plan for the GAA Results API"

  api_stages {
    api_id = aws_api_gateway_rest_api.gaa_results.id
    stage  = aws_api_gateway_stage.gaa_results.stage_name
  }
}

resource "aws_api_gateway_usage_plan_key" "gaa_results" {
  key_id        = aws_api_gateway_api_key.gaa_results.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.gaa_results.id
}

output "gaa_results_api_url" {
  description = "Base URL for the GAA Results API."
  value       = "https://${aws_api_gateway_rest_api.gaa_results.id}.execute-api.${data.aws_region.current.region}.amazonaws.com/${aws_api_gateway_stage.gaa_results.stage_name}"
}

output "gaa_results_api_key_id" {
  description = "ID of the API Gateway API key."
  value       = aws_api_gateway_api_key.gaa_results.id
}

output "gaa_results_api_key_value" {
  description = "Value of the API Gateway API key. Treat this as sensitive."
  value       = aws_api_gateway_api_key.gaa_results.value
  sensitive   = true
}
