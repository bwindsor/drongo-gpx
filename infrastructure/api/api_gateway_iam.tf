/* API execution role */
resource "aws_iam_role" "iam_for_api_gateway" {
  name = "${var.deployment_name}-api-gateway-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["apigateway.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

/* Policy attached to API gateway role to allow execution of lambda */
resource "aws_iam_role_policy" "api_gateway_execute_lambda_policy" {
    name = "${var.deployment_name}-execute-lambda-policy"
    role = aws_iam_role.iam_for_api_gateway.id

    policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "${join("\",\"", var.lambda_arns)}"
            ]
        }
    ]
}
EOF
}
