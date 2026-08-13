# Arquitectura — DataLake Pipeline AWS

## Diagrama

​```mermaid
flowchart LR
    KAGGLE["Dataset Kaggle<br/>(origen simulado)"] -->|"upload mensual"| RAW

    subgraph S3["S3 — datalake-ventas"]
        RAW["raw/sales/ingest_date=YYYY-MM/"]
        PROC["processed/"]
        CUR["curated/"]
    end

    subgraph VPC["VPC 10.0.0.0/16"]
        subgraph PRIV["Subred privada"]
            EC2["EC2 + Auto Scaling"]
            EP["VPC Endpoint → S3"]
        end
    end

    RAW --> EC2
    EC2 --> EP --> S3
    EC2 --> PROC
    EC2 --> CUR
    CUR -->|"UPSERT"| RDS["RDS PostgreSQL"]

    IAM["IAM: batch-role<br/>(min. privilegio por prefijo)"] -.->|"rol asumido"| EC2
​```

## Componentes

| Componente local | Equivalente cloud | Identidad / credencial |
|---|---|---|
| LocalStack IAM (`batch-role`) | AWS IAM Role | `sts:AssumeRole`, credenciales temporales (15 min) |
| LocalStack S3 (`datalake-ventas`) | Amazon S3 | Acceso vía `batch-role` + bucket policy (dos capas) |
| Terraform (`iac/`) | Terraform contra AWS real | Local: `test`/`test`. Prod: credenciales reales, sin hardcodear |
| EC2 + Auto Scaling | Amazon EC2 + Auto Scaling Group | Instance profile → `batch-role`, sin access keys en la instancia |
| VPC | Amazon VPC | Subred privada + Security Groups referenciados entre sí |
| RDS | Amazon RDS PostgreSQL | Credencial en Secrets Manager, leída en runtime |


## Decisiones de identidad

- Los servicios se autentican entre sí sólo con roles IAM asumidos vía STS — nunca con access keys de larga duración guardadas en algún lado.
- `batch-role` es la única identidad con acceso al bucket, y el acceso está acotado por prefijo: sólo lee `raw/`, lee y escribe `processed/` y `curated/`, no puede borrar nada en ningún lado.
- Las credenciales que devuelve `assume-role` expiran a los 15 minutos — en AWS real esto lo renueva solo el servicio (EC2 vía IMDSv2), nadie las toca a mano.
- La credencial de RDS vive en Secrets Manager, nunca en el código ni en variables de entorno commiteadas.