resource "aws_dynamodb_table" "league_table" {
  name         = "gaa-results-leagues-${local.environment}"
  billing_mode = "PAY_PER_REQUEST" # on‑demand capacity

  hash_key = "league_code"

  attribute {
    name = "league_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  tags = {
    Environment = local.environment
  }
}

resource "aws_dynamodb_table" "league_clubs_table" {
  name         = "gaa-results-league-clubs-${local.environment}"
  billing_mode = "PAY_PER_REQUEST" # on‑demand capacity

  hash_key = "league_code"
  range_key = "team_code"

  attribute {
    name = "league_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  attribute {
    name = "team_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  tags = {
    Environment = local.environment
  }
}

resource "aws_dynamodb_table" "league_results_table" {
  name         = "gaa-results-league-results-${local.environment}"
  billing_mode = "PAY_PER_REQUEST" # on‑demand capacity

  hash_key = "match_code"
  range_key = "league_code"

  attribute {
    name = "match_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  attribute {
    name = "league_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  tags = {
    Environment = local.environment
  }
}

resource "aws_dynamodb_table" "league_matches_table" {
  name         = "gaa-results-league-matches-${local.environment}"
  billing_mode = "PAY_PER_REQUEST" # on‑demand capacity

  hash_key = "match_code"
  range_key = "league_code"

  attribute {
    name = "match_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  attribute {
    name = "league_code"
    type = "S"      # string type; up to 10 characters/digits
  }

  tags = {
    Environment = local.environment
  }
}