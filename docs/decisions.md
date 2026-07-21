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
