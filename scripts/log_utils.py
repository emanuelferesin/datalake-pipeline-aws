"""Logger compartido: manda cada linea a CloudWatch Logs ademas de stdout."""
import time

import boto3

LOG_GROUP = "/datalake/batch"

logs = boto3.client(
    "logs",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)


def get_logger(nombre_script):
    log_stream = f"{nombre_script}-{int(time.time())}"
    logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=log_stream)

    def log(mensaje):
        print(mensaje)
        logs.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=log_stream,
            logEvents=[{"timestamp": int(time.time() * 1000), "message": mensaje}],
        )

    return log
