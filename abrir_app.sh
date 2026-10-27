#!/usr/bin/env bash
set -euo pipefail
diretorio=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
mkdir -p "$diretorio/dados"
exec python3 "$diretorio/app.py" >> "$diretorio/dados/app.log" 2>&1 < /dev/null
