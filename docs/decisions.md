# Decision log

Registro de decisiones de arquitectura del proyecto.

## Formato (ADR)

```text
### NNN — Título corto de la decisión

Decision: qué decidiste hacer.
Contexto: qué te llevó a esta decisión.
Alternativas: qué otras opciones consideraste.
Tradeoff: qué ganás y qué cedés.
Resultado: qué quedó implementado.
```

## Decisiones

### 001 — Usamos un rol IAM en vez de guardar una clave fija

Decision: la instancia que procesa los datos usa un rol (batch-role) que le da
AWS temporalmente, en vez de tener una clave guardada en algún lado.

Contexto: el proceso necesita leer los archivos de raw/, y leer y escribir en
processed/ y curated/. Pero no tiene por qué poder escribir en raw/ (ahí sólo
llegan los datos originales, no se tocan) ni borrar nada. Si usábamos una clave
fija y se filtraba, quedaba activa para siempre. Con el rol, la credencial vence
sola a los 15 minutos.

Alternativas que pensamos: darle una clave de usuario fija (más simple pero
más peligroso), o darle permiso total sobre el bucket para no complicarnos
(mucho más fácil, pero si algo falla puede romper cualquier cosa).

Tradeoff: nos llevó más laburo escribir permisos separados por carpeta que uno
solo genérico, pero así si el rol se compromete el daño es limitado — no puede
tocar raw/ ni borrar nada en ningún lado.

Resultado: probamos que funciona con sts assume-role, la credencial que devuelve
vence en 15 minutos (lo vimos en el campo Expiration).

### 002 — Bucket datalake-ventas con seguridad y marcador de procesado por lote
Decision: el bucket arranca con Block Public Access, encryption SSE-S3 y versioning
ON antes de subir nada, mas una bucket policy que solo deja pasar a batch-role.
Para saber que lotes ya se procesaron, cada carpeta de raw/ va a tener un archivo
_PROCESSED cuando el batch job termino con ese lote.

Contexto: la carga del dataset a raw/ la hacemos a mano, asi que no podemos confiar en que siempre se haga bien o a tiempo.
El marcador evita reprocesar lo que ya esta hecho y deja ver de un vistazo que
lotes faltan.
Alternativas: un manifest unico con todos los lotes procesados (mas facil de leer
pero si se rompe ese archivo se pierde el estado de todo el historial).
Tradeoff: un archivo por carpeta es mas verboso, pero si se corrompe uno solo
afecta a ese lote, no a todos.
Resultado: bucket datalake-ventas con BPA + encryption + versioning + bucket
policy, y la convencion de _PROCESSED (se creara recien
cuando armemos el batch job en la fase de EC2).

### 003 — Subida mensual simulada en vez de subir todo el dataset junto

Decision: escribimos un script (simulate_ingesta_mensual.py) que sube el dataset
mes a mes a raw/sales/ingest_date=YYYY-MM/, en vez de subir el CSV completo de una.
Antes de subir, chequea con head_object si ese mes ya esta en el bucket y si esta,
no hace nada.

Contexto: el dataset de Kaggle es un archivo estatico con 2 años de facturas, pero
nuestra arquitectura esta pensada para lotes que llegan de a uno por mes. Si
subiamos todo junto no ibamos a poder demostrar que el pipeline procesa solo lo
nuevo, que es justo lo que le mostramos al profesor que ibamos a resolver.

Alternativas: subir el CSV entero de una y particionarlo recien en el
procesamiento (mas simple, pero no simula una llegada real, y no probamos la
idempotencia en la parte de ingesta).

Tradeoff: hay que correr el script varias veces (uno por mes) en vez de una sola
carga, pero asi el bucket queda armado exactamente como se veria en la vida real,
con historia y con huecos que se van llenando.

Resultado: 4 de los 25 meses del dataset ya estan en el bucket (dic 2009 a
marzo 2010), el resto lo vamos subiendo mas adelante corriendo el mismo script.