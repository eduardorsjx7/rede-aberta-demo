#!/usr/bin/env bash
set -euo pipefail
diretorio=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
mkdir -p "$diretorio/dados"
if [ -t 1 ]; then
  echo "Rede aberta: o painel da equipe vai abrir no navegador."
  echo "No painel, \"Abrir telão\" abre a apresentação para o projetor."
  echo "Deixe esta janela aberta durante a palestra. Para encerrar o app, aperte Ctrl+C."
  # No Terminal, mostra as mensagens do app e também as guarda no log.
  python3 "$diretorio/app.py" < /dev/null 2>&1 | tee -a "$diretorio/dados/app.log"
else
  exec python3 "$diretorio/app.py" >> "$diretorio/dados/app.log" 2>&1 < /dev/null
fi
