#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
REPO='https://github.com/SigmaDX007/cesta-justa-piracicaba.git'
command -v git >/dev/null 2>&1 || { echo 'Git nao encontrado.' >&2; exit 1; }
[ -d .git ] || { echo 'Esta copia nao possui .git. Use o ZIP versionado ou inicialize o Git.' >&2; exit 1; }
if git remote get-url origin >/dev/null 2>&1; then
  current="$(git remote get-url origin)"
  [ "$current" = "$REPO" ] || { echo "origin inesperado: $current" >&2; exit 1; }
else
  git remote add origin "$REPO"
fi
printf 'Publicando somente a branch main em %s\n' "$REPO"
git push --set-upstream origin main
