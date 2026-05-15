
# Install dependencies
resource "null_resource" "lambda_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/lambda_scraper/requirements.txt")
    source       = filemd5("${path.module}/lambda_scraper/lambda_function.py")
  }

  provisioner "local-exec" {
    command = "pip3 install -r ${path.module}/lambda_scraper/requirements.txt -t ${path.module}/lambda_scraper/"
  }
}

# Zip the Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_scraper/"
  output_path = "${path.module}/lambda_scraper/lambda.zip"
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
      DYNAMODB_CLUBS_TABLE = aws_dynamodb_table.league_clubs_table.name
      DYNAMODB_RESULTS_TABLE = aws_dynamodb_table.league_results_table.name
      DYNAMODB_MATCHES_TABLE = aws_dynamodb_table.league_matches_table.name
    }
  }
}

# Install dependencies for the league table calculator lambda
resource "null_resource" "lambda_table_calc_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/lambda_league_table_calc/requirements.txt")
    source       = filemd5("${path.module}/lambda_league_table_calc/lambda_function.py")
  }

  provisioner "local-exec" {
    command = "pip3 install -r ${path.module}/lambda_league_table_calc/requirements.txt -t ${path.module}/lambda_league_table_calc/"
  }
}

# Zip the league table calculator Lambda code
data "archive_file" "lambda_table_calc_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_league_table_calc/"
  output_path = "${path.module}/lambda_league_table_calc/lambda.zip"
  depends_on  = [null_resource.lambda_table_calc_dependencies]
}

# Lambda Function for league table calculations
resource "aws_lambda_function" "league_table_calc" {
  function_name    = "league-table-calc"
  runtime          = "python3.12"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.lambda_role.arn
  filename         = data.archive_file.lambda_table_calc_zip.output_path
  source_code_hash = data.archive_file.lambda_table_calc_zip.output_base64sha256

  timeout = 300

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.league_table.name
    }
  }
}