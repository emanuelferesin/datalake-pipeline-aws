# DataLake Pipeline AWS

Proyecto integrador del módulo Cloud Computing (ITBA).

> > **Integrantes:** Emanuel Feresin, Sebastián Castro, Federico Cavasin

Arquitectura: VPC + IAM + S3 + Cómputo + Base de datos, provisionada con Terraform contra LocalStack/Docker (local-first), con AWS real como referencia.

Pipeline: un dataset de ventas (Kaggle, `online_retail_II`) se ingesta mes a mes a `raw/`, se procesa a `processed/`/`curated/`, y se carga a PostgreSQL vía UPSERT. Ver [docs/architecture.md](docs/architecture.md) para el diagrama completo.

---

## Cómo correrlo end-to-end

### 1. Levantar los servicios locales

```bash
docker compose up -d
```

Esto levanta LocalStack (IAM, STS, S3, EC2, Secrets Manager) y Postgres.

### 2. Provisionar la infraestructura con Terraform

```bash
cd iac
terraform init
terraform plan
terraform apply
```

Esto crea, en un solo comando: el rol `batch-role` (+ trust policy + policy S3/SQS/Logs), el bucket `datalake-ventas` (Block Public Access, encryption SSE-S3, versioning, bucket policy), la VPC con subred privada + VPC endpoint a S3, la EC2 con instance profile, el secret de Secrets Manager con la credencial de Postgres, la cola SQS `datalake-lotes-pendientes` y el log group de CloudWatch `/datalake/batch`.

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Correr el pipeline

```bash
# Subir un mes del dataset a raw/ (idempotente: no repite si ya está subido)
# Al subir, avisa el lote nuevo encolando un mensaje en SQS
python scripts/simulate_ingesta_mensual.py --mes 2009-12

# Procesa los lotes avisados por SQS: raw/ -> processed/ + curated/
python scripts/procesar_lote.py

# Carga curated/ a la tabla ventas_por_pais en Postgres (UPSERT)
python scripts/cargar_curated.py
```

Los 3 scripts loguean cada paso también en CloudWatch Logs (`/datalake/batch`), no solo por stdout.

---

## Estructura del repo

```
.
├── compose.yaml           # LocalStack + Postgres
├── docs/
│   ├── architecture.md    # Diagrama y componentes
│   └── decisions.md       # ADRs (10+ decisiones documentadas)
├── iam/
│   ├── trust_policy.json       # EC2 assume role
│   ├── batch_role_policy.json  # Permisos de batch-role por prefijo (S3 + SQS + Logs)
│   └── README.md
├── s3/
│   └── bucket_policy.json # Bucket policy: solo batch-role puede acceder
├── scripts/
│   ├── simulate_ingesta_mensual.py  # Ingesta mensual simulada (idempotente), avisa por SQS
│   ├── procesar_lote.py             # Consume SQS, raw/ -> processed/ + curated/
│   ├── cargar_curated.py            # curated/ -> Postgres (UPSERT)
│   ├── log_utils.py                 # Logger compartido hacia CloudWatch Logs
│   └── README.md
├── sql/
│   └── 001_schema.sql     # Tabla ventas_por_pais
├── iac/
│   ├── main.tf             # IAM role + S3 bucket + VPC + EC2 + Secrets Manager + SQS + CloudWatch Logs
│   ├── aws-local.tf        # Provider AWS apuntando a LocalStack
│   ├── variables.tf        # project_name, environment, region
│   ├── outputs.tf          # bucket_name, batch_role_arn, queue_url, log_group_name
│   └── README.md
├── requirements.txt        # boto3, duckdb, psycopg2, pytest
└── bin/init.sh
```

Mirar [iac/README.md](iac/README.md) para más detalle del setup de Terraform.

---

## Estado del proyecto

- [x] `docs/architecture.md` con diagrama y componentes
- [x] `docs/decisions.md` con ADRs documentados
- [x] `iam/` + `s3/` con los JSON de la solución (trust + policies + bucket policy)
- [x] `iac/main.tf` provisiona IAM + S3 + VPC + EC2 + Secrets Manager + SQS + CloudWatch Logs con Terraform
- [x] `scripts/` con 3 demos automatizados e idempotentes (ingesta, procesamiento, carga)
- [x] `compose.yaml` con los servicios (LocalStack, Postgres)
- [ ] Tests unitarios (`pytest`)

---

## Referencias del curso

- Repo de demos por clase: [cloud-foundations-lab](https://github.com/maxflorentin/cloud-foundations-lab)
- AWS Academy Cloud Architecting (Spanish LATAM): los módulos cubren la teoría
- `cloud-foundations-lab` tiene labs 04 (IAM), 05 (EC2), 06 (S3), 07 (VPC), 08 (RDS) — usar como referencia
