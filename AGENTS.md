# Repository Guidelines

## Project Structure & Module Organization

This is a small Linux demonstration of an open Wi-Fi network with a local educational page. All files live at the repository root:

- `servidor.py`: Python standard-library HTTP server, embedded HTML/CSS, consent validation, and JSON Lines recording.
- `iniciar.sh`: creates the temporary NetworkManager access point, starts the server, and removes the connection profile on exit.
- `clientes.sh`: displays the interface's IP/MAC neighbor table without writing records.
- `README.md`: equipment requirements and presentation instructions in Portuguese.
- `registros.jsonl`: runtime participant data; treat it as private output.

There are no separate asset, test, or package directories.

## Build, Test, and Development Commands

No build step or Python package installation is required. The full demonstration needs Linux, NetworkManager (`nmcli`), Python 3, `iproute2`, and an AP-capable Wi-Fi adapter.

- `python3 servidor.py --host 127.0.0.1 --port 8080 --log /tmp/rede-aberta-test.jsonl`: runs locally without changing network settings.
- `bash iniciar.sh wlan0`: starts the open access point and page at `http://10.42.0.1:8080`; replace `wlan0` with the actual interface. This invokes `sudo` and changes that interface's connection. Stop with `Ctrl+C`.
- `bash clientes.sh wlan0`: lists observed neighbors.
- `bash -n iniciar.sh clientes.sh`: checks shell syntax without executing the scripts.

## Coding Style & Naming Conventions

Follow existing conventions: four-space Python indentation, two-space Bash block indentation, `snake_case` functions and variables, and PascalCase classes. Keep Portuguese user-facing text and descriptive Portuguese identifiers consistent. Retain Bash strict mode (`set -euo pipefail`) and quote shell expansions. No formatter or linter is configured.

## Testing Guidelines

No automated framework or coverage threshold is configured. For server changes, use the loopback command above with disposable records. Verify page rendering, unknown-route rejection, consent rejection without recording, valid submissions producing one JSON line, and invalid or oversized input rejection. For network changes, check access-point connectivity and profile cleanup on exit using demonstration equipment.

## Commit & Pull Request Guidelines

This directory has no Git metadata, so no existing commit convention can be established. If versioned, use concise imperative subjects, such as `Fix consent validation`. Pull requests should explain behavior changes and verification performed; link relevant issues and include screenshots for page changes.

## Participant Data & Configuration

Preserve explicit consent before recording and disabled automatic request logging. Never commit participant records. Use disposable log paths during development and remove presentation records when no longer needed.
