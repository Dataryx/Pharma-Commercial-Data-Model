.PHONY: setup generate build test docs demo all clean erd load lint

SCALE ?= demo
SEED ?= 42
PYTHON ?= python
DBT_DIR := dbt
WH := $(CURDIR)/warehouse/pcdm.duckdb

setup:
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m pcdm init-db
	cd $(DBT_DIR) && dbt deps --profiles-dir profiles

generate:
	$(PYTHON) -m pcdm generate --scale $(SCALE) --seed $(SEED)

load:
	$(PYTHON) -m pcdm load --scale $(SCALE)

build: load
	set PCDM_DUCKDB_PATH=$(WH) && cd $(DBT_DIR) && dbt build --profiles-dir profiles --target duckdb

test:
	$(PYTHON) -m pytest tests -q
	set PCDM_DUCKDB_PATH=$(WH) && cd $(DBT_DIR) && dbt test --profiles-dir profiles --target duckdb

docs:
	cd $(DBT_DIR) && dbt docs generate --profiles-dir profiles --target duckdb
	$(PYTHON) -m pcdm docs-generate
	mkdocs build --strict || true

erd:
	$(PYTHON) -m pcdm erd

demo:
	$(PYTHON) -m streamlit run apps/commercial_insights/Home.py --server.headless true

lint:
	ruff check src tests apps
	black --check src tests apps

all: setup generate build test docs
	@echo "PCDM all complete (scale=$(SCALE) seed=$(SEED))"

clean:
	$(PYTHON) -m pcdm clean --scale $(SCALE)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages $(DBT_DIR)/logs || true
