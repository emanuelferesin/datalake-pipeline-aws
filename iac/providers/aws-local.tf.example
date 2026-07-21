# Provider AWS apuntando a LocalStack (local-first del curso).
#
# Para usar: renombrar a aws-local.tf
# Para AWS real: quitar `endpoints {}` y configurar credenciales reales.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  # Credenciales falsas — LocalStack las ignora
  access_key = "test"
  secret_key = "test"

  # Flags que LocalStack necesita
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  # Endpoints apuntando a LocalStack
  endpoints {
    s3             = "http://localhost:4566"
    iam            = "http://localhost:4566"
    sts            = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    sns            = "http://localhost:4566"
  }
}
