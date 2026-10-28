#!/usr/bin/env python3
"""Abre só a prévia do telão (docs/previa_telao.html) no navegador, sem rodar o app."""

import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent
webbrowser.open((BASE / "docs" / "previa_telao.html").as_uri())
print("Prévia aberta. Setas mudam de etapa; D = resultados; C = comparação; F = tela cheia.")
