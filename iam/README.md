# `iam/` — políticas y trust documents del proyecto

Acá van los JSON que defina tu solución:

- **Trust policies** — quién puede asumir un rol (ej. EC2, Lambda, ECS task)
- **Identity policies** — qué puede hacer una identidad (usuario/rol/grupo)
- **Resource policies** — qué identidades dejá entrar un recurso (ej. bucket policy)

`trust_policy.json` arranca como ejemplo molde (rol asumible por EC2). Modificá / borrá / agregá lo que necesite tu arquitectura.

Referencias en el lab del curso:
- Lab 04 — `iam/s3_read_policy.json` muestra una identity policy de privilegio mínimo
- Lab 06 — `s3/bucket_policy.json` muestra una resource policy con Principal=rol
