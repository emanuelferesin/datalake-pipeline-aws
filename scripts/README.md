# `scripts/` — demos automatizados del proyecto

Acá van los scripts (Python o shell) que orquestan tu solución end-to-end.

Convenciones que vienen del curso:
- **Idempotentes** — se pueden correr dos veces sin romper
- **Sin secretos hardcodeados** — leen credenciales del entorno o de Secrets Manager
- **Auto-documentados** — el output narra qué se hizo y dónde quedó

Referencias en el lab del curso:
- `scripts/iam_demo.py` — patrón de orquestación + idempotencia
- `scripts/ec2_demo.py` — uso de tags para detectar recursos existentes
- `scripts/s3_demo.py` — head_object para idempotencia por contenido
- `scripts/vpc_demo.py` — find-by-tag helper para grafo de recursos
