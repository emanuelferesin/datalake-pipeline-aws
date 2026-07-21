variable "project_name" {
  type        = string
  description = "Slug del proyecto. Se usa para nombrar recursos."
  default     = "mi-proyecto"
}

variable "environment" {
  type        = string
  description = "Entorno: dev / staging / prod"
  default     = "dev"
}

variable "region" {
  type        = string
  description = "Región del provider elegido"
  default     = "us-east-1"
}
