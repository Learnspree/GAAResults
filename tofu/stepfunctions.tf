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
                    Next = "InvokeLambda"
                }
                InvokeLambda = {
                    Type = "Task"
                    Resource = "arn:aws:states:::lambda:invoke"
                    Parameters = {
                        FunctionName = aws_lambda_function.scraper.arn
                        Payload = {
                            "league_id.$" = "$.current"
                        }
                    }
                    Next = "IsLast"
                }
                IsLast = {
                    Type = "Choice"
                    Choices = [
                        {
                            Variable = "$.current"
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
                    # increment current using intrinsic function
                    Parameters = {
                        "from.$" = "$.from"
                        "to.$"   = "$.to"
                        "current.$" = "States.MathAdd($.current, 1)"
                    }
                    Next = "InvokeLambda"
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
                Resource = "${aws_lambda_function.scraper.arn}:*"
            }
        ]
    })
}