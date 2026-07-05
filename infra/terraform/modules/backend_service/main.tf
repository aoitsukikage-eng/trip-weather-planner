variable "resource_group_name" {
  type        = string
  description = "Resource group that contains backend resources."
}

variable "location" {
  type        = string
  description = "Azure region for backend resources."
}

variable "container_registry_name" {
  type        = string
  description = "Azure Container Registry name."
}

variable "log_analytics_workspace_name" {
  type        = string
  description = "Log Analytics workspace name for Container Apps."
}

variable "container_app_environment_name" {
  type        = string
  description = "Container Apps environment name."
}

variable "container_app_name" {
  type        = string
  description = "Container App name for the FastAPI backend."
}

variable "backend_image" {
  type        = string
  description = "Container image for the backend."
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

variable "frontend_origin" {
  type        = string
  description = "Public frontend origin allowed by backend CORS."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to backend resources."
  default     = {}
}

resource "azurerm_container_registry" "backend" {
  name                = var.container_registry_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = var.tags
}

resource "azurerm_log_analytics_workspace" "backend" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_container_app_environment" "backend" {
  name                       = var.container_app_environment_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.backend.id

  tags = var.tags
}

resource "azurerm_container_app" "backend" {
  name                         = var.container_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.backend.id
  revision_mode                = "Single"

  secret {
    name  = "acr-admin-password"
    value = azurerm_container_registry.backend.admin_password
  }

  secret {
    name  = "cwa-api-key"
    value = var.cwa_api_key
  }

  registry {
    server               = azurerm_container_registry.backend.login_server
    username             = azurerm_container_registry.backend.admin_username
    password_secret_name = "acr-admin-password"
  }

  ingress {
    external_enabled = true
    target_port      = var.target_port

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = var.cpu
      memory = var.memory

      env {
        name  = "CACHE_TTL_SECONDS"
        value = tostring(var.cache_ttl_seconds)
      }

      env {
        name  = "CORS_ORIGINS"
        value = var.frontend_origin
      }

      env {
        name  = "UPSTREAM_TIMEOUT_SECONDS"
        value = tostring(var.upstream_timeout_seconds)
      }

      env {
        name        = "CWA_API_KEY"
        secret_name = "cwa-api-key"
      }
    }
  }

  tags = var.tags
}

output "container_registry_login_server" {
  description = "ACR login server."
  value       = azurerm_container_registry.backend.login_server
}

output "container_app_name" {
  description = "Backend Container App name."
  value       = azurerm_container_app.backend.name
}

output "container_app_fqdn" {
  description = "Backend Container App FQDN."
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "container_app_url" {
  description = "Backend Container App HTTPS URL."
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}
