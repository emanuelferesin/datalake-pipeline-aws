"""Carga curated/ a la tabla ventas_por_pais en postgres, via UPSERT.
La credencial se lee de Secrets Manager en runtime, nunca hardcodeada.
"""
import csv
import io
import json

import boto3
import psycopg2

BUCKET = "datalake-ventas"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

secrets = boto3.client(
    "secretsmanager",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)


def obtener_credencial():
    resp = secrets.get_secret_value(SecretId="app/db")
    return json.loads(resp["SecretString"])


def crear_schema(conn):
    with open("sql/001_schema.sql") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def listar_lotes_curated():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="curated/sales/", Delimiter="/")
    return [p["Prefix"] for p in resp.get("CommonPrefixes", [])]


def cargar_lote(conn, prefijo):
    key = f"{prefijo}ventas_por_pais.csv"
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    contenido = obj["Body"].read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contenido))

    filas = 0
    with conn.cursor() as cur:
        for row in reader:
            cur.execute(
                """
                INSERT INTO ventas_por_pais (country, ingest_date, total_amount, total_facturas)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (country, ingest_date)
                DO UPDATE SET
                    total_amount = EXCLUDED.total_amount,
                    total_facturas = EXCLUDED.total_facturas
                """,
                (row["Country"], row["ingest_date"], row["total_amount"], row["total_facturas"]),
            )
            filas += 1
    conn.commit()
    print(f"{prefijo}: {filas} filas cargadas (UPSERT)")


if __name__ == "__main__":
    cred = obtener_credencial()

    conn = psycopg2.connect(
        host=cred["host"],
        port=cred["port"],
        dbname=cred["dbname"],
        user=cred["username"],
        password=cred["password"],
    )

    crear_schema(conn)

    for prefijo in listar_lotes_curated():
        cargar_lote(conn, prefijo)

    conn.close()