"""Sube el dataset de ventas a S3 particionado por mes, simulando la
llegada de un reporte mensual. Idempotente: no vuelve a subir un mes
que ya está en el bucket.
"""
import argparse
import json
import os
import re
import sys
import tempfile

import boto3
import duckdb

from log_utils import get_logger

BUCKET = "datalake-ventas"
QUEUE_NAME = "datalake-lotes-pendientes"
CSV_LOCAL = "data/raw/online_retail_II.csv"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

log = get_logger("simulate_ingesta_mensual")


def conectar_dataset():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW ventas AS SELECT * FROM read_csv_auto('{CSV_LOCAL}', header=True)")
    return con


def listar_meses(con):
    return con.execute(
        "SELECT DISTINCT strftime(InvoiceDate, '%Y-%m') AS mes "
        "FROM ventas ORDER BY 1"
    ).fetchall()


def ya_subido(mes):
    key = f"raw/sales/ingest_date={mes}/ventas.csv"
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False


def avisar_lote_pendiente(mes, prefijo):
    queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"mes": mes, "prefijo": prefijo}),
    )
    log(f"{mes}: aviso encolado en {QUEUE_NAME}")


def subir_mes(con, mes):
    if not re.fullmatch(r"\d{4}-\d{2}", mes):
        print(f"Formato de mes invalido: {mes} (esperado YYYY-MM)")
        sys.exit(1)

    key = f"raw/sales/ingest_date={mes}/ventas.csv"
    if ya_subido(mes):
        log(f"{mes}: ya estaba subido ({key}), no se repite")
        return

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    con.execute(
        f"COPY (SELECT * FROM ventas WHERE strftime(InvoiceDate, '%Y-%m') = '{mes}') "
        f"TO '{tmp_path}' (HEADER, DELIMITER ',')"
    )

    s3.upload_file(tmp_path, BUCKET, key)
    os.remove(tmp_path)
    log(f"{mes}: subido a s3://{BUCKET}/{key}")
    avisar_lote_pendiente(mes, f"raw/sales/ingest_date={mes}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mes", help="Mes a subir, formato YYYY-MM")
    parser.add_argument("--list", action="store_true", help="Lista los meses disponibles en el CSV")
    args = parser.parse_args()

    con = conectar_dataset()

    if args.list:
        for (mes,) in listar_meses(con):
            estado = "subido" if ya_subido(mes) else "pendiente"
            log(f"{mes}  [{estado}]")
        sys.exit(0)

    if not args.mes:
        log("Usar --list para ver meses disponibles, o --mes YYYY-MM para subir uno")
        sys.exit(1)

    subir_mes(con, args.mes)