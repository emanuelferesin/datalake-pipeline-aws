# Tus recursos van acá.
#
# Sugerencia de estructura cuando crezca:
#   - main.tf           ← root, orquesta módulos
#   - modules/network/  ← VPC, subnets, SGs
#   - modules/identity/ ← IAM roles, policies
#   - modules/compute/  ← EC2 / Lambda / containers
#   - modules/data/     ← S3 / RDS / DynamoDB
#
# Ejemplo de recurso (descomentá según provider elegido):
#
# resource "aws_s3_bucket" "data" {
#   bucket = "${var.project_name}-data"
# }
