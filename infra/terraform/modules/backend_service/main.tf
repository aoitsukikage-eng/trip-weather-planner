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

variable "request_timeout_seconds" {
  type    = number
  default = 30
}

variable "min_instance_count" {
  type    = number
  default = 0
}

variable "max_instance_count" {
  type    = number
  default = 2
}

variable "non_secret_env" {
  type    = map(string)
  default = {}
}

variable "secret_env" {
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

# FastAPI backend on Cloud Run (scales to zero; stable HTTPS URL).
resource "google_cloud_run_v2_service" "backend" {
  name                = var.service_name
  location            = var.region
  project             = var.project_id
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    timeout = "${var.request_timeout_seconds}s"

    containers {
      image = var.backend_image
      ports {
        container_port = 8080
      }

      dynamic "env" {
        for_each = var.non_secret_env
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secrets (CWA_API_KEY, GEMINI_API_KEY, TDX_*) are injected from
      # Secret Manager in production rather than baked into the image.
      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }
    }
    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
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

output "service_name" {
  value = google_cloud_run_v2_service.backend.name
}
