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

### 004 — Pasamos IAM y S3 de comandos sueltos a Terraform

Decision: en vez de dejar el rol y el bucket armados a mano con comandos awslocal
(como quedaron en las fases 2 y 3), los pasamos a Terraform (iac/main.tf), que
lee los mismos JSON que ya teniamos (trust_policy.json, batch_role_policy.json,
bucket_policy.json) sin reescribir nada.

Contexto: no habia codigo que levante la infra descripta en los ADRs —
todo lo habiamos hecho tipeando en la terminal, no quedaba nada
reproducible. Ademas probamos en vivo que LocalStack Community pierde el estado
con un simple "docker compose restart localstack" (no hace falta ni que pase
tiempo) — el rol y el bucket desaparecen. Corrimos terraform plan despues del
restart y detecto solo los 2 recursos borrados, sin duplicar nada: plan limpio
de 7 a crear, 0 a cambiar, 0 a destruir. Eso confirma que la recuperacion es
"terraform apply de nuevo", nada mas.

Alternativas: escribir un script Python que repita los comandos (mas rapido de
armar, pero sigue siendo imperativo — hay que acordarse de correrlo entero y en
orden). Terraform en cambio es declarativo: describis el estado final y el
compara contra lo que existe, por eso detecta solo lo que falta.

Tradeoff: hubo que instalar Terraform a mano en el Codespace (no venia en el
devcontainer, ya lo agregamos para el proximo) y debuggear por que el provider
no se aplicaba — resulto ser que Terraform solo lee archivos .tf de la carpeta
donde corres el comando, no de subcarpetas, asi que iac/providers/aws-local.tf
nunca se estaba usando hasta que lo movimos a iac/aws-local.tf.

Resultado: terraform apply desde iac/ levanta el rol, las 3 policies y el bucket
completo (BPA + encryption + versioning) en un solo comando, 7 recursos, probado
dos veces incluyendo una recuperacion despues de perder el estado de LocalStack.

### 005 — VPC solo con subred privada, sin Internet Gateway ni NAT

Decision: la red del proyecto tiene una sola subred, privada, sin salida a
Internet. El unico camino que tiene hacia afuera es un VPC endpoint Gateway
hacia S3.

Contexto: el batch job no sirve nada por HTTP ni recibe conexiones de nadie —
solo lee y escribe en S3. 

Alternativas: agregar subred publica + Internet Gateway igual, por si despues
hace falta (por ejemplo para instalar paquetes en el arranque de la EC2 via
apt/pip). O agregar un NAT Gateway para dar salida controlada.

Tradeoff: si en algun momento el batch job necesita salir a Internet de verdad
(una libreria que no esta en el user-data, una API externa), no va a poder —
hay que agregar NAT explicitamente, con su costo. Elegimos no pagar ni exponer
nada que no usamos todavia.

Resultado: VPC 10.0.0.0/16, subred privada 10.0.2.0/24, VPC endpoint Gateway a
S3 verificado (route table con ruta al prefix list de S3, estado "available").
Sin IGW, sin subred publica, sin NAT.

### 006 — EC2 fija en vez de Auto Scaling Group (limite de LocalStack Community)

Decision: en vez de un Auto Scaling Group (min=0, max=2, escala a demanda),
provisiono una sola instancia EC2 fija con el instance profile de batch-role.

Contexto: intenté crear el ASG con Terraform y LocalStack Community me devolvió
501 "API for service autoscaling not yet implemented or pro feature" — es
función paga, no se arregla con configuración. Me pasó lo mismo que con RDS
en el lab 08.

Alternativas: podía dejar el código del ASG en el repo sin aplicarlo
(documentado pero no probado), o pivotar a un recurso que sí se pudiera crear
y verificar de verdad. Elegí la segunda, para no dejar código "de mentira"
en el repo.

Tradeoff: perdí la posibilidad de probar el escalado real en este entorno.
En AWS real, el diseño seguiría siendo un ASG con desired_capacity=0 en reposo,
que escala a 1 cuando llega un lote nuevo (con un trigger que queda fuera del
alcance del proyecto, no cursé EventBridge/Lambda) y vuelve a 0 al terminar.

Resultado: creé la instancia EC2 única (i-04cb3878b1990dbfe) con instance
profile, security group y subred privada, todo verificado. Dejo el diseño
de Auto Scaling documentado como la versión de producción, no como algo que
esté corriendo ahora.