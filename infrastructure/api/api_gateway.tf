/* Main API spec */
locals {
  stage_name = "prod"
}

resource "aws_api_gateway_rest_api" "api" {
    name        = "${var.deployment_name} API"
    description = "API for SpeedCube"
    body        = data.template_file.api-spec.rendered
}

resource "aws_api_gateway_deployment" "api-deployment" {
    depends_on = [data.template_file.api-spec]

    rest_api_id = aws_api_gateway_rest_api.api.id
    stage_name  = local.stage_name

    variables = {
      "api_spec_hash" = "${sha256(data.template_file.api-spec.rendered)}"
    }
}

data "template_file" "api-spec" {
    template = "${file("${path.module}/api_spec.yaml")}"

    vars = {
        deployment_name = var.deployment_name
        lambda_exec_role_arn = aws_iam_role.iam_for_api_gateway.arn
        lambda_make_gpx_arn = var.lambda_make_gpx_arn
    }
}


/* Throttle limits */
resource "aws_api_gateway_method_settings" "api_throttle_setting" {
  depends_on = [aws_api_gateway_deployment.api-deployment]

  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_deployment.api-deployment.stage_name
  method_path = "*/*"

  settings {
    throttling_burst_limit = 1000
    throttling_rate_limit = 2000

    metrics_enabled = true
    logging_level   = "INFO"
  }

}
