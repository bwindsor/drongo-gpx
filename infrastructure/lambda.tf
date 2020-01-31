data "archive_file" "lambda_function_make_gpx" {
    type        = "zip"
    output_path = "artifacts/lambda_make_gpx.zip"

    source {
      content = file("../make_gpx.py")
      filename = "make_gpx.py"
    }
}

resource "aws_lambda_function" "lambda_make_gpx" {
  filename      = data.archive_file.lambda_function_make_gpx.output_path
  function_name = "${local.deployment_name}-make-gpx"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "make_gpx.handler"

  source_code_hash = data.archive_file.lambda_function_make_gpx.output_base64sha256

  runtime = "python3.7"
  timeout = 15
  memory_size = 512
  description = "Make a DrongO GPX"
}


data "archive_file" "lambda_function_shift_purple_pen" {
    type        = "zip"
    output_path = "artifacts/lambda_shift_purple_pen.zip"

    source {
      content = file("../shift_purple_pen.py")
      filename = "shift_purple_pen.py"
    }

  source {
    content = file("../multipart_decoder.py")
    filename = "multipart_decoder.py"
  }
}

resource "aws_lambda_function" "lambda_shift_purple_pen" {
  filename      = data.archive_file.lambda_function_shift_purple_pen.output_path
  function_name = "${local.deployment_name}-shift-purple-pen"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "shift_purple_pen.handler"

  source_code_hash = data.archive_file.lambda_function_shift_purple_pen.output_base64sha256

  runtime = "python3.7"
  timeout = 15
  memory_size = 512
  description = "Shift a PurplePen file"
}
