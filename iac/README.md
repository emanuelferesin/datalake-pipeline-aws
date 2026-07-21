# `iac/` — Infrastructure as Code

Tu infraestructura definida en Terraform. El starter te deja la estructura — vos elegís el provider y agregás recursos.

## Cómo funciona

```
iac/
├── main.tf              ← tus recursos
├── variables.tf         ← inputs configurables (project_name, region, etc.)
├── outputs.tf           ← lo que querés exponer
└── providers/
    ├── aws-local.tf.example     ← AWS contra LocalStack
    ├── azure-local.tf.example   ← Azure contra Azurite
    └── gcp-local.tf.example     ← GCP contra fake-gcs / cloud-storage emulator
```

## Setup

1. Elegí UN provider y renombrá su archivo `.tf.example` → `.tf`:

   ```bash
   # Para AWS local
   mv iac/providers/aws-local.tf.example iac/providers/aws-local.tf

   # O para Azure local
   mv iac/providers/azure-local.tf.example iac/providers/azure-local.tf

   # O para GCP local
   mv iac/providers/gcp-local.tf.example iac/providers/gcp-local.tf
   ```

2. Inicializá:

   ```bash
   cd iac
   terraform init
   ```

3. Aplicá:

   ```bash
   terraform plan
   terraform apply
   ```

## Madurez de cada combinación

| Provider local | Estado | Notas |
|---|---|---|
| AWS + LocalStack (community) | ✅ probado | la combinación estándar del curso |
| AWS + ministack / Floci | ⚠️ experimental | drop-in replacement de LocalStack |
| Azure + Azurite | ⚠️ solo storage | Azurite emula Blob; otros servicios Azure no |
| GCP + fake-gcs-server | ⚠️ solo storage | similar a Azurite — alcance limitado |

Para AWS real / Azure real / GCP real, remové el endpoint custom de los providers y configurá credenciales reales.

## Convenciones

- **Un módulo por capa** (network, identity, compute, data) si el proyecto crece
- **Variables tipadas y con descripción** — `terraform validate` te ayuda
- **No commitear `.tfstate`** (ya está en .gitignore)
- **Backend remoto en prod** (S3 + DynamoDB lock para AWS; equivalentes para los otros)
