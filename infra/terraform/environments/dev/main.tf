# Dev environment: wires the reusable modules together.
# Demo target = Cloud Run backend + GCS-hosted static frontend (the master plan's
# "actual demo deployment"). The AWS mapping lives in docs/cloud_architecture.md
# as the design reference; this is the concrete IaC that provisions the demo.

module "backend_service" {
  source                  = "../../modules/backend_service"
  project_id              = var.project_id
  region                  = var.region
  service_name            = var.backend_service_name
  backend_image           = var.backend_image
  request_timeout_seconds = var.request_timeout_seconds
  min_instance_count      = var.min_instance_count
  max_instance_count      = var.max_instance_count
  non_secret_env = {
    CACHE_TTL_SECONDS        = tostring(var.cache_ttl_seconds)
    CORS_ORIGINS             = var.frontend_origin
    UPSTREAM_TIMEOUT_SECONDS = tostring(var.upstream_timeout_seconds)
  }
  secret_env = var.backend_secret_env
}

module "frontend_hosting" {
  source      = "../../modules/frontend_hosting"
  bucket_name = var.frontend_bucket_name
  location    = var.region
}

output "backend_url" {
  description = "Public HTTPS URL of the Cloud Run backend."
  value       = module.backend_service.service_url
}

output "frontend_bucket" {
  description = "Static frontend bucket."
  value       = module.frontend_hosting.bucket_name
}

output "frontend_website_url" {
  description = "Static website endpoint for the frontend bucket."
  value       = module.frontend_hosting.website_url
}

output "backend_service_name" {
  description = "Cloud Run service name."
  value       = module.backend_service.service_name
}
