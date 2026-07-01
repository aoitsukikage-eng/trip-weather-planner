# Dev environment: wires the reusable modules together.
# Demo target = Cloud Run backend + GCS-hosted static frontend (the master plan's
# "actual demo deployment"). The AWS mapping lives in docs/cloud_architecture.md
# as the design reference; this is the concrete IaC that provisions the demo.

module "backend_service" {
  source        = "../../modules/backend_service"
  project_id    = var.project_id
  region        = var.region
  service_name  = "twp-api"
  backend_image = var.backend_image
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
