
# Install dependencies
resource "null_resource" "lambda_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/lambda/requirements.txt")
    source       = filemd5("${path.module}/lambda/lambda_function.py")
  }

  provisioner "local-exec" {
    command = "pip3 install -r ${path.module}/lambda/requirements.txt -t ${path.module}/lambda/"
  }
}

# Zip the Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/"
  output_path = "${path.module}/lambda.zip"
  depends_on  = [null_resource.lambda_dependencies]
}

# Lambda Function
resource "aws_lambda_function" "scraper" {
  function_name    = "league-scraper"
  runtime          = "python3.12"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.lambda_role.arn
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout = 300  # 5 minutes, adjust as needed

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.league_table.name
    }
  }
}