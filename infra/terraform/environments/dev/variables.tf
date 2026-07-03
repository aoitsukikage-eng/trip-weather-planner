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

variable "backend_service_name" {
  type        = string
  description = "Cloud Run service name for the backend API."
  default     = "twp-api"
}

variable "frontend_origin" {
  type        = string
  description = "Public frontend origin allowed by backend CORS, e.g. https://demo.example.com."
  default     = "https://demo.example.com"
}

variable "cache_ttl_seconds" {
  type        = number
  description = "Backend cache TTL passed to Cloud Run."
  default     = 1800
}

variable "upstream_timeout_seconds" {
  type        = number
  description = "Timeout for upstream API calls passed to Cloud Run."
  default     = 10
}

variable "request_timeout_seconds" {
  type        = number
  description = "Cloud Run request timeout in seconds."
  default     = 30
}

variable "min_instance_count" {
  type        = number
  description = "Minimum Cloud Run instances."
  default     = 0
}

variable "max_instance_count" {
  type        = number
  description = "Maximum Cloud Run instances."
  default     = 2
}

variable "backend_secret_env" {
  description = "Secret Manager bindings for backend env vars such as CWA_API_KEY."
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}
