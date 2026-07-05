locals {
  common_tags = {
    app         = "trip-weather-planner"
    environment = "demo"
    managed_by  = "terraform"
  }
}

resource "azurerm_resource_group" "demo" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

module "backend_service" {
  source = "../../modules/backend_service"

  resource_group_name            = azurerm_resource_group.demo.name
  location                       = azurerm_resource_group.demo.location
  container_registry_name        = var.container_registry_name
  log_analytics_workspace_name   = var.log_analytics_workspace_name
  container_app_environment_name = var.container_app_environment_name
  container_app_name             = var.container_app_name
  backend_image                  = var.backend_image
  cwa_api_key                    = var.cwa_api_key
  cache_ttl_seconds              = var.cache_ttl_seconds
  upstream_timeout_seconds       = var.upstream_timeout_seconds
  min_replicas                   = var.min_replicas
  max_replicas                   = var.max_replicas
  cpu                            = var.cpu
  memory                         = var.memory
  target_port                    = var.target_port
  frontend_origin                = var.frontend_origin
  tags                           = local.common_tags
}

module "frontend_hosting" {
  source = "../../modules/frontend_hosting"

  storage_account_name = var.frontend_storage_account_name
  resource_group_name  = azurerm_resource_group.demo.name
  location             = azurerm_resource_group.demo.location
  tags                 = local.common_tags
}

output "backend_url" {
  description = "Public HTTPS URL of the backend Container App."
  value       = module.backend_service.container_app_url
}

output "backend_container_app_name" {
  description = "Backend Container App name."
  value       = module.backend_service.container_app_name
}

output "container_registry_login_server" {
  description = "ACR login server."
  value       = module.backend_service.container_registry_login_server
}

output "frontend_storage_account_name" {
  description = "Static frontend Storage account name."
  value       = module.frontend_hosting.storage_account_name
}

output "frontend_primary_web_endpoint" {
  description = "Static website endpoint for the frontend."
  value       = module.frontend_hosting.primary_web_endpoint
}
