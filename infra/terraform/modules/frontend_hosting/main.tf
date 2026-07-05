variable "storage_account_name" {
  type        = string
  description = "Globally unique Storage account name for the static frontend."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group that contains the frontend Storage account."
}

variable "location" {
  type        = string
  description = "Azure region for the frontend Storage account."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to frontend hosting resources."
  default     = {}
}

resource "azurerm_storage_account" "frontend" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"

  static_website {
    index_document     = "index.html"
    error_404_document = "index.html"
  }

  tags = var.tags
}

output "storage_account_name" {
  description = "Frontend Storage account name."
  value       = azurerm_storage_account.frontend.name
}

output "primary_web_endpoint" {
  description = "Static website endpoint for the frontend."
  value       = azurerm_storage_account.frontend.primary_web_endpoint
}
