variable "project_id" {
  type        = string
  description = "GCP project id for the demo deployment."
  default     = "trip-weather-planner-dev"
}

variable "region" {
  type        = string
  description = "GCP region for Cloud Run."
  default     = "asia-east1"
}

variable "backend_image" {
  type        = string
  description = "Container image for the FastAPI backend (Artifact Registry URL)."
  default     = "asia-east1-docker.pkg.dev/trip-weather-planner-dev/twp/backend:latest"
}

variable "frontend_bucket_name" {
  type        = string
  description = "Globally-unique bucket name for the static frontend."
  default     = "trip-weather-planner-frontend-dev"
}
