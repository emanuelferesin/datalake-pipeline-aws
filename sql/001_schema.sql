CREATE TABLE IF NOT EXISTS ventas_por_pais (
    country VARCHAR NOT NULL,
    ingest_date VARCHAR NOT NULL,
    total_amount NUMERIC NOT NULL,
    total_facturas INTEGER NOT NULL,
    PRIMARY KEY (country, ingest_date)
);