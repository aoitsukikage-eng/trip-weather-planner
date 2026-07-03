variable "bucket_name" {
  type = string
}

variable "location" {
  type = string
}

# Static frontend hosting via IaC (satisfies "IaC 建置前端架構").
# A GCS website bucket; in production a CDN + TLS sits in front. On Cloudflare
# Pages this module would be swapped for the cloudflare_pages_project resource.
resource "google_storage_bucket" "frontend" {
  name                        = var.bucket_name
  location                    = var.location
  force_destroy               = true
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html" # SPA fallback
  }
}

resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

output "bucket_name" {
  value = google_storage_bucket.frontend.name
}

output "website_url" {
  value = "http://${google_storage_bucket.frontend.name}.storage.googleapis.com"
}
