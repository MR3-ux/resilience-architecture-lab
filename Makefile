.PHONY: help validate quality test demo fragile clean

PYTHON ?= python3
ENV = PYTHONPATH=src

help:
	@echo "Targets: validate quality test demo fragile clean"

validate:
	$(ENV) $(PYTHON) -m resilience_lab validate examples/azure-active-active.json
	$(ENV) $(PYTHON) -m resilience_lab validate examples/fragile-single-region.json

test:
	$(ENV) $(PYTHON) -m unittest discover -s tests -v

quality:
	$(PYTHON) scripts/quality.py
	shellcheck scripts/demo.sh

demo: validate quality test
	$(ENV) $(PYTHON) -m resilience_lab assess examples/azure-active-active.json --output-dir reports/demo
	$(ENV) $(PYTHON) -m resilience_lab simulate examples/azure-active-active.json --scenario east-region-loss

fragile:
	$(ENV) $(PYTHON) -m resilience_lab assess examples/fragile-single-region.json --output-dir reports/fragile

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(p) for p in [Path('reports/latest'), Path('reports/ci'), Path('reports/fragile')] if p.exists()]"
