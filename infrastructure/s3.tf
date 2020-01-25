resource "aws_s3_bucket" "website_bucket" {
  bucket = "drongo-gpx"
  acl    = "public-read"

  website {
    index_document = "index.html"
  }
}

output "website_url" {
  value = aws_s3_bucket.website_bucket.website_endpoint
}

resource "aws_s3_bucket_object" "index_file" {
  bucket = aws_s3_bucket.website_bucket.id
  acl = "public-read"
  content_type = "text/html"
  key = "index.html"
  content = data.template_file.index_html.rendered
  etag = md5(data.template_file.index_html.rendered)
}

data "template_file" "index_html" {
  template = file("../index.html")

  vars = {
    API_INVOKE_URL = "${module.api.api_invoke_url}"
  }
}