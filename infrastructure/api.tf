module api {
  source = "./api"

  deployment_name = local.deployment_name
  lambda_arns = [aws_lambda_function.lambda_make_gpx.arn]
  layers = []
  lambda_make_gpx_arn = aws_lambda_function.lambda_make_gpx.invoke_arn
}

/* Permission on lambda's end to allow API gateway to invoke it */
resource "aws_lambda_permission" "allow_api_gateway" {
    statement_id   = "${aws_lambda_function.lambda_make_gpx.function_name}-allow-api-gateway"
    action         = "lambda:InvokeFunction"
    function_name  = aws_lambda_function.lambda_make_gpx.function_name
    principal      = "apigateway.amazonaws.com"
    source_arn     = module.api.execution_arn
}

output "api_invoke_url" {
  value = module.api.api_invoke_url
}

output "api_execution_arn" {
  value = module.api.execution_arn
}
