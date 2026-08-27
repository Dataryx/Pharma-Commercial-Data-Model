.PHONY: setup generate build test docs demo all clean erd load lint

SCALE ?= demo
SEED ?= 42
PYTHON ?= python

setup:
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m pcdm init-db
	cd transform && dbt deps --profiles-dir profiles

generate:
	$(PYTHON) -m pcdm generate --scale $(SCALE) --seed $(SEED)

load:
	$(PYTHON) -m pcdm load --scale $(SCALE)

build: load
	set PCDM_DUCKDB_PATH=$(CURDIR)/warehouse/pcdm.duckdb && cd transform && dbt build --profiles-dir profiles --target duckdb

test:
	$(PYTHON) -m pytest tests -q
	set PCDM_DUCKDB_PATH=$(CURDIR)/warehouse/pcdm.duckdb && cd transform && dbt test --profiles-dir profiles --target duckdb

docs:
	cd transform && dbt docs generate --profiles-dir profiles --target duckdb
	$(PYTHON) -m pcdm docs-generate
	mkdocs build --strict || true

erd:
	$(PYTHON) -m pcdm erd

demo:
	$(PYTHON) -m streamlit run app/Home.py --server.headless true

lint:
	ruff check src tests app
	black --check src tests app

all: setup generate build test docs
	@echo "PCDM all complete (scale=$(SCALE) seed=$(SEED))"

clean:
	$(PYTHON) -m pcdm clean --scale $(SCALE)
	rm -rf transform/target transform/dbt_packages .duckdb transform/logs || true
