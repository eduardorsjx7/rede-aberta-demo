# Repository Guidelines

## Project Structure & Module Organization

Local Linux demonstration of an open Wi-Fi network, part of the extension project "Inclusão Digital e Segurança da Informação". Code lives at the repository root; documentation lives in `docs/`.

- `app.py`: local control panel server (stdlib HTTP), serves `interface/` and the `/api/*` endpoints.
- `controle.py`: session state, steps, NetworkManager operations and cleanup.
- `servidor.py`: participant page (`http://10.42.0.1:8080`), consent validation, JSON Lines recording.
- `comparacao.py`: HTTP × HTTPS comparison lab (TCP bridges, local TLS certificate).
- `interface/`: team panel (`index.html`, `app.js`, `estilo.css`), projected screen (`telao.html`, `telao.css`) and step texts (`conteudo.js`, shared by both).
- `iniciar.sh`, `clientes.sh`, `abrir_app.sh`, `instalar_atalho.py`: command-line helpers and desktop shortcut.
- `docs/`: `CONTEXTO_PROJETO.md` (link to the deck), `ROTEIRO_APRESENTACAO.md`, `GUIA_SLIDES_DINAMICA.md`.
- `tests/`: `unittest` suites and `verificar_interface.cjs` (Playwright).
- `dados/`, `registros.jsonl`: runtime participant data; private, never committed.

## Build, Test, and Development Commands

No build step or package installation. The full demonstration needs Linux, NetworkManager (`nmcli`), Python 3, OpenSSL, `iproute2` and an AP-capable Wi-Fi adapter.

- `python3 -m unittest discover -s tests -v`: automated tests (simulated network, temporary directories).
- `bash -n abrir_app.sh iniciar.sh clientes.sh`: shell syntax check.
- `python3 app.py --sem-navegador`: starts the panel without opening a browser, then `node tests/verificar_interface.cjs` checks the UI (needs Playwright; use an isolated server).
- `bash iniciar.sh wlan0`: legacy script that starts the open access point; uses `sudo` and changes that interface's connection.

## Coding Style & Naming Conventions

Four-space Python indentation, two-space Bash indentation, `snake_case` functions and variables, PascalCase classes. Keep Portuguese user-facing text and descriptive Portuguese identifiers. Retain `set -euo pipefail` in Bash and quote expansions. Telão styling follows the project deck (see `docs/CONTEXTO_PROJETO.md`); keep telão text large (stage is 1920 × 1080) and in short sentences for the EJA audience. No formatter or linter is configured.

## Testing Guidelines

Run the unit tests after any server, control or comparison change. For interface changes also run `tests/verificar_interface.cjs`; it checks that the seven telão steps do not overlap the footer. Rehearse the physical access point with a phone before presenting.

## Commit & Pull Request Guidelines

Use concise imperative subjects, such as `Fix consent validation`. Pull requests should explain behavior changes and verification performed and include screenshots for telão or page changes.

## Participant Data & Configuration

Preserve explicit consent before recording. Never commit participant records, certificates or keys (see `.gitignore`). Use disposable log paths during development and remove presentation records when no longer needed.
