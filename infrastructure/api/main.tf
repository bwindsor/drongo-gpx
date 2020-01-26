output "execution_arn" {
  value = aws_api_gateway_deployment.api-deployment.execution_arn
}

output "api_invoke_url" {
  value = aws_api_gateway_deployment.api-deployment.invoke_url
}

output "api_base_url" {
  value = replace(aws_api_gateway_deployment.api-deployment.invoke_url, "//${local.stage_name}$/", "")
}

output "full_api_spec" {
  value = data.template_file.api-spec.rendered
}
