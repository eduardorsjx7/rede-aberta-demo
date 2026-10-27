#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Uso: $0 <interface-wifi>  (ex.: wlan0)" >&2
  exit 2
fi

echo "Vizinhos observados na interface $1 (IP, MAC e estado):"
ip neigh show dev "$1"
echo "A lista pode ficar vazia ate o aparelho acessar a pagina ou gerar trafego."
