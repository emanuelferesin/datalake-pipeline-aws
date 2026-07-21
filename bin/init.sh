#!/usr/bin/env bash
# Personaliza el starter con el nombre del proyecto.
#
# Uso:
#   ./bin/init.sh "Nombre del Proyecto"
#
# Reemplaza el placeholder {{PROJECT_NAME}} en docs y README.
# Los integrantes del grupo se listan en docs/architecture.md.

set -euo pipefail

PROJECT_NAME="${1:-}"

if [[ -z "$PROJECT_NAME" ]]; then
  echo "Uso: $0 \"Nombre del Proyecto\""
  echo "Ej:  $0 \"Smart City Toll\""
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ Personalizando starter en: $ROOT"
echo "  Proyecto: $PROJECT_NAME"
echo

FILES=(
  "$ROOT/README.md"
  "$ROOT/docs/architecture.md"
)

for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    sed -i.bak "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$f"
    rm -f "$f.bak"
    echo "  ✓ $f"
  fi
done

echo
echo "Listo. Próximos pasos sugeridos:"
echo "  1. Agregá los integrantes del grupo al README.md"
echo "  2. Editá compose.yaml con los servicios que tu arquitectura usa"
echo "  3. Completá docs/architecture.md con tu diagrama"
echo "  4. Documentá tu primera decisión en docs/decisions.md"
echo "  5. git init && git add . && git commit -m 'init: starter personalizado'"
