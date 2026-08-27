#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

export PYTHONPATH="$repo_root/src"
python3 -m unittest discover -s tests -v
python3 -m resilience_lab validate examples/azure-active-active.json
python3 -m resilience_lab assess examples/azure-active-active.json --output-dir reports/demo
python3 -m resilience_lab simulate examples/azure-active-active.json --scenario east-region-loss
