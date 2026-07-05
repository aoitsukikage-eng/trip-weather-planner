variable "resource_group_name" {
  type        = string
  description = "Azure resource group for the demo deployment."
  default     = "rg-twp-demo"
}

variable "location" {
  type        = string
  description = "Azure region for all demo resources."
  default     = "southeastasia"
}

variable "container_registry_name" {
  type        = string
  description = "Azure Container Registry name for backend images."
  default     = "twpacr4316"
}

variable "log_analytics_workspace_name" {
  type        = string
  description = "Log Analytics workspace name for Container Apps."
  default     = "twp-log-analytics"
}

variable "container_app_environment_name" {
  type        = string
  description = "Azure Container Apps environment name."
  default     = "twp-ca-env"
}

variable "container_app_name" {
  type        = string
  description = "Backend Container App name."
  default     = "twp-backend"
}

variable "backend_image" {
  type        = string
  description = "Container image for the backend."
  default     = "twpacr4316.azurecr.io/twp-backend:latest"
}

variable "frontend_storage_account_name" {
  type        = string
  description = "Storage account name for the static frontend."
  default     = "twpfe5ce0"
}

variable "frontend_origin" {
  type        = string
  description = "Public frontend origin allowed by backend CORS."
  default     = "https://twpfe5ce0.z23.web.core.windows.net"
}

variable "cwa_api_key" {
  type        = string
  description = "CWA API key injected into the backend Container App."
  sensitive   = true
}

variable "cache_ttl_seconds" {
  type        = number
  description = "Backend cache TTL in seconds."
  default     = 1800
}

variable "upstream_timeout_seconds" {
  type        = number
  description = "Timeout for upstream API calls in seconds."
  default     = 10
}

variable "min_replicas" {
  type        = number
  description = "Minimum Container App replicas."
  default     = 0
}

variable "max_replicas" {
  type        = number
  description = "Maximum Container App replicas."
  default     = 1
}

variable "cpu" {
  type        = number
  description = "Container CPU allocation."
  default     = 0.5
}

variable "memory" {
  type        = string
  description = "Container memory allocation."
  default     = "1Gi"
}

variable "target_port" {
  type        = number
  description = "Backend ingress target port."
  default     = 8080
}
