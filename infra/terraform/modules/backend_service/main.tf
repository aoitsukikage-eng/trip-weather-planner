variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_name" {
  type = string
}

variable "backend_image" {
  type = string
}

# FastAPI backend on Cloud Run (scales to zero; stable HTTPS URL).
resource "google_cloud_run_v2_service" "backend" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.backend_image
      ports {
        container_port = 8080
      }
      # Secrets (CWA_API_KEY, GEMINI_API_KEY, TDX_*) are injected from
      # Secret Manager in production rather than baked into the image.
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }
}

# Public, unauthenticated access for the demo API.
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.backend.uri
}
