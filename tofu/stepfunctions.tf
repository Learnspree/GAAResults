resource "aws_sfn_state_machine" "league_loop" {
    name       = "league-loop-workflow"
    role_arn   = aws_iam_role.stepfunctions_role.arn
        definition = jsonencode({
            Comment = "Loop from 'from' to 'to' calling Lambda for each league id with pauses"
            StartAt = "Init"
            States = {
                Init = {
                    Type = "Pass"
                    # initialize working state with from, to and current
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "$.from"
                    }
                    Next = "ComputeCandidate"
                }
                ComputeCandidate = {
                    Type = "Pass"
                    # compute candidate end = current + 9
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "$.current"
                        "candidate.$" = "States.MathAdd($.current, 9)"
                    }
                    Next = "CompareCandidate"
                }
                CompareCandidate = {
                    Type = "Choice"
                    Choices = [
                        {
                            Variable = "$.candidate"
                            NumericGreaterThanEqualsPath = "$.to"
                            Next = "SetBatchToTo"
                        }
                    ]
                    Default = "SetBatchToCandidate"
                }
                SetBatchToTo = {
                    Type = "Pass"
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "$.current"
                        "batch_end.$" = "$.to"
                    }
                    Next = "InvokeLambda"
                }
                SetBatchToCandidate = {
                    Type = "Pass"
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "$.current"
                        "batch_end.$" = "$.candidate"
                    }
                    Next = "InvokeLambda"
                }
                InvokeLambda = {
                    Type = "Task"
                    Resource = "arn:aws:states:::lambda:invoke"
                    ResultPath = null
                    Parameters = {
                        FunctionName = aws_lambda_function.scraper.arn
                        Payload = {
                            "from.$" = "$.current"
                            "to.$"   = "$.batch_end"
                        }
                    }
                    Next = "IsLast"
                }
                IsLast = {
                    Type = "Choice"
                    Choices = [
                        {
                            Variable = "$.batch_end"
                            NumericGreaterThanEqualsPath = "$.to"
                            Next = "Success"
                        }
                    ]
                    Default = "PauseOneMinute"
                }
                PauseOneMinute = {
                    Type = "Wait"
                    Seconds = 60
                    Next = "Increment"
                }
                Increment = {
                    Type = "Pass"
                    # set current to batch_end + 1
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "States.MathAdd($.batch_end, 1)"
                    }
                    Next = "ComputeCandidate"
                }
                Success = {
                    Type = "Succeed"
                }
            }
        })
}

resource "aws_iam_role" "stepfunctions_role" {
    name = "stepfunctions-execution-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "states.amazonaws.com"
                }
            }
        ]
    })
}

resource "aws_iam_role_policy" "stepfunctions_lambda_policy" {
  name = "stepfunctions-lambda-policy"
  role = aws_iam_role.stepfunctions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.scraper.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}