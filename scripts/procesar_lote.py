"""Procesa los lotes de raw/ que todavia no tienen marcador _PROCESSED:
limpia el CSV, calcula el total de linea, y escribe processed/ y curated/.
Es lo que en AWS real correria como user-data de la EC2 (LocalStack Community
no lo ejecuta, por eso lo corro manual).
"""
import os
import sys
import tempfile

import boto3
import duckdb

BUCKET = "datalake-ventas"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)


def lotes_pendientes():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/sales/", Delimiter="/")
    prefijos = [p["Prefix"] for p in resp.get("CommonPrefixes", [])]

    pendientes = []
    for prefijo in prefijos:
        marker_key = f"{prefijo}_PROCESSED"
        try:
            s3.head_object(Bucket=BUCKET, Key=marker_key)
        except s3.exceptions.ClientError:
            pendientes.append(prefijo)
    return pendientes


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

    print(f"{mes}: procesado -> {proc_key} y {cur_key}")


if __name__ == "__main__":
    pendientes = lotes_pendientes()

    if not pendientes:
        print("No hay lotes pendientes de procesar")
        sys.exit(0)

    for prefijo in pendientes:
        procesar_lote(prefijo)