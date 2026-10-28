#!/usr/bin/env python3
"""Instala atalhos do app para o usuário atual, sem precisar de sudo."""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent


def aspas_exec(texto):
    valor = str(texto).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return f'"{valor}"'


def instalar_macos():
    # No macOS, um arquivo .command abre com duplo clique no Terminal e deixa o app rodando em segundo plano.
    conteudo = ('#!/bin/bash\n'
                f'nohup bash {shlex.quote(str(BASE / "abrir_app.sh"))} >/dev/null 2>&1 &\n'
                'echo "Rede aberta: o painel vai abrir no navegador. Pode fechar esta janela."\n')
    atalhos = [BASE / 'Rede Aberta.command']
    mesa = Path.home() / 'Desktop'
    if mesa.is_dir():
        atalhos.append(mesa / 'Rede Aberta.command')
    for atalho in atalhos:
        if atalho.exists() and atalho.parent != BASE and str(BASE / 'abrir_app.sh') not in atalho.read_text(encoding='utf-8'):
            print(f'Atalho existente preservado: {atalho}')
            continue
        atalho.write_text(conteudo, encoding='utf-8')
        atalho.chmod(0o755)
        print(f'Atalho pronto: {atalho}')


def main():
    if sys.platform == 'darwin':
        instalar_macos()
        return
    conteudo = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Rede aberta
Comment=Controlar a dinâmica e abrir o telão da apresentação
Exec={aspas_exec(BASE / 'abrir_app.sh')}
Path={BASE}
Icon={BASE / 'interface' / 'icone.svg'}
Terminal=false
Categories=Education;
StartupNotify=false
'''
    atalhos = [BASE / 'Rede Aberta.desktop']
    aplicativos = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
    aplicativos.mkdir(parents=True, exist_ok=True)
    atalhos.append(aplicativos / 'rede-aberta-demo.desktop')
    try:
        desktop = subprocess.run(['xdg-user-dir', 'DESKTOP'], check=True, capture_output=True, text=True).stdout.strip()
        if desktop and Path(desktop).is_dir() and Path(desktop) != Path.home():
            atalhos.append(Path(desktop) / 'Rede Aberta.desktop')
    except (OSError, subprocess.CalledProcessError):
        pass
    for atalho in atalhos:
        if atalho.exists() and atalho.parent != BASE:
            anterior = atalho.read_text(encoding='utf-8')
            if str(BASE / 'abrir_app.sh') not in anterior:
                print(f'Atalho existente preservado: {atalho}')
                continue
        atalho.write_text(conteudo, encoding='utf-8')
        atalho.chmod(0o755)
        if shutil.which('gio'):
            subprocess.run(['gio', 'set', str(atalho), 'metadata::trusted', 'true'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f'Atalho pronto: {atalho}')
    if shutil.which('update-desktop-database'):
        subprocess.run(['update-desktop-database', str(aplicativos)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
