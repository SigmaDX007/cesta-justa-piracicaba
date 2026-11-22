#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo 'Python 3.10+ nao encontrado. Instale Python e reexecute.' >&2
  exit 1
fi
"$PY" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ obrigatorio"'
exec "$PY" server.py "$@"
