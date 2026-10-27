#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Uso: $0 <interface-wifi>  (ex.: wlan0)" >&2
  exit 2
fi

interface=$1
perfil=Extensao-Rede-Aberta
ssid=EXTENSAO-REDE-ABERTA
diretorio=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

for programa in nmcli python3 ip; do
  if ! command -v "$programa" >/dev/null 2>&1; then
    echo "Programa necessario nao encontrado: $programa" >&2
    exit 1
  fi
done

if ! nmcli device status | awk 'NR > 1 {print $1}' | grep -Fxq -- "$interface"; then
  echo "Interface nao encontrada: $interface" >&2
  exit 1
fi

if nmcli connection show "$perfil" >/dev/null 2>&1; then
  echo "Ja existe uma conexao chamada $perfil. Remova-a ou altere o nome no script." >&2
  exit 1
fi

sudo nmcli connection add type wifi ifname "$interface" con-name "$perfil" \
  autoconnect no ssid "$ssid" \
  802-11-wireless.mode ap \
  802-11-wireless.band bg \
  802-11-wireless.ap-isolation yes \
  ipv4.method shared \
  ipv4.addresses 10.42.0.1/24 \
  ipv6.method disabled

limpar() {
  sudo nmcli connection down "$perfil" >/dev/null 2>&1 || true
  sudo nmcli connection delete "$perfil" >/dev/null 2>&1 || true
}
trap limpar EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

sudo nmcli connection up "$perfil" ifname "$interface"

echo "Rede aberta: $ssid"
echo "Pagina da demonstracao: http://10.42.0.1:8080"
echo "Para encerrar e apagar o perfil temporario, pressione Ctrl+C."
python3 "$diretorio/servidor.py" --host 10.42.0.1 --port 8080
