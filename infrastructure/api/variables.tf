variable "deployment_name" {
    description = "Name of the deployment"
    type = string
}

variable "lambda_make_gpx_arn" {
  type = string
}

variable "lambda_shift_purple_pen_arn" {
  type = string
}

variable "lambda_arns" {
  type = list(string)
  description = "List of Lambda ARNs which API gateway should have permission to invoke"
}

variable "layers" {
  description = "Lambda layer ARNs to use"
  type = list(string)
  default = []
}