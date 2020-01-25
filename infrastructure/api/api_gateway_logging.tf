/* Global account config for api writing to cloudwatch */
resource "aws_api_gateway_account" "global_api_role" {
  cloudwatch_role_arn = aws_iam_role.api_cloudwatch_role.arn
}

/* This is used by api gateway to write to cloudwatch */
resource "aws_iam_role" "api_cloudwatch_role" {
  name = "${var.deployment_name}-api-gateway-cloudwatch-global"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

/* Role allowing API gateway to use write logs */
resource "aws_iam_role_policy" "cloudwatch" {
  name = "${var.deployment_name}-global-api-cloudwatch-policy"
  role = aws_iam_role.api_cloudwatch_role.id

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:GetLogEvents",
                "logs:FilterLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}
