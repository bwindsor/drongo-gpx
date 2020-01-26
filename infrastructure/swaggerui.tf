data "template_file" "api_spec_for_swagger_docs" {
  template = module.api.full_api_spec

  vars = {
    api_base_url = module.api.api_invoke_url
  }
}

resource "aws_s3_bucket_object" "api_definition_file" {
  bucket = aws_s3_bucket.website_bucket.id
  acl    = "public-read"
  content_type = "application/x-yaml"
  key = "swagger-ui/swagger.yaml"
  content = data.template_file.api_spec_for_swagger_docs.rendered
  etag = md5(data.template_file.api_spec_for_swagger_docs.rendered)
}

resource "aws_s3_bucket_object" "website_public_files_user" {
  for_each = fileset("files/swagger-ui", "**")

  bucket = aws_s3_bucket.website_bucket.id
  acl    = "public-read"
  content_type = lookup(var.mime_types, element(split(".",each.value), length(split(".",each.value))-1))
  key    = "swagger-ui/${each.value}"
  source = "files/swagger-ui/${each.value}"
  etag   = filemd5("files/swagger-ui/${each.value}")
}

variable "mime_types" {
  default = {
    htm = "text/html"
    html = "text/html"
    css = "text/css"
    js = "text/javascript"
    map = "text/javascript"
    json = "application/json"
    png = "image/png"
    ico = "image/x-icon"
    svg = "image/svg+xml"
    gif = "image/gif"
    gpx = "application/gpx+xml"
    txt = "text/plain"
  }
  type = map(string)
}

output "swagger_ui_url" {
  value = "${aws_s3_bucket.website_bucket.website_endpoint}/swagger-ui/index.html"
}
