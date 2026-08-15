"""Procesa los lotes de raw/ que todavia no tienen marcador _PROCESSED:
limpia el CSV, calcula el total de linea, y escribe processed/ y curated/.
Es lo que en AWS real correria como user-data de la EC2 (LocalStack Community
no lo ejecuta, por eso lo corro manual). Los lotes a procesar se toman de la
cola SQS datalake-lotes-pendientes, avisada por simulate_ingesta_mensual.py.
"""
import json
import os
import sys
import tempfile

import boto3
import duckdb

from log_utils import get_logger

BUCKET = "datalake-ventas"
QUEUE_NAME = "datalake-lotes-pendientes"

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

log = get_logger("procesar_lote")


def recibir_mensajes_pendientes():
    queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    resp = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2
    )
    mensajes = resp.get("Messages", [])
    return queue_url, mensajes


def ya_procesado(prefijo):
    marker_key = f"{prefijo}_PROCESSED"
    try:
        s3.head_object(Bucket=BUCKET, Key=marker_key)
        return True
    except s3.exceptions.ClientError:
        return False


def procesar_lote(prefijo):
    mes = prefijo.split("ingest_date=")[1].rstrip("/")
    raw_key = f"{prefijo}ventas.csv"

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_raw:
        raw_local = tmp_raw.name
    s3.download_file(BUCKET, raw_key, raw_local)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW raw AS SELECT * FROM read_csv_auto('{raw_local}', header=True)")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_proc:
        proc_local = tmp_proc.name

    con.execute(f"""
        COPY (
            SELECT *, Quantity * Price AS LineTotal
            FROM raw
            WHERE Quantity > 0 AND Price > 0
        ) TO '{proc_local}' (HEADER, DELIMITER ',')
    """)

    proc_key = f"processed/sales/ingest_date={mes}/ventas_procesado.csv"
    s3.upload_file(proc_local, BUCKET, proc_key)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_cur:
        cur_local = tmp_cur.name

    con.execute(f"""
        COPY (
            SELECT
                Country,
                '{mes}' AS ingest_date,
                SUM(Quantity * Price) AS total_amount,
                COUNT(DISTINCT Invoice) AS total_facturas
            FROM raw
            WHERE Quantity > 0 AND Price > 0
            GROUP BY Country
        ) TO '{cur_local}' (HEADER, DELIMITER ',')
    """)

    cur_key = f"curated/sales/ingest_date={mes}/ventas_por_pais.csv"
    s3.upload_file(cur_local, BUCKET, cur_key)

    marker_key = f"{prefijo}_PROCESSED"
    s3.put_object(Bucket=BUCKET, Key=marker_key, Body=b"")

    os.remove(raw_local)
    os.remove(proc_local)
    os.remove(cur_local)

    log(f"{mes}: procesado -> {proc_key} y {cur_key}")


if __name__ == "__main__":
    queue_url, mensajes = recibir_mensajes_pendientes()

    if not mensajes:
        log("No hay avisos pendientes en la cola")
        sys.exit(0)

    for mensaje in mensajes:
        cuerpo = json.loads(mensaje["Body"])
        prefijo = cuerpo["prefijo"]

        if ya_procesado(prefijo):
            log(f"{cuerpo['mes']}: ya tenia marcador _PROCESSED, se descarta el aviso")
        else:
            procesar_lote(prefijo)

        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=mensaje["ReceiptHandle"])