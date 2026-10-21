CONFIG ?= config.json
UV_CACHE_DIR ?= $(CURDIR)/.uv-cache
export UV_CACHE_DIR
UV = uv run --no-sync

install:
	uv sync --frozen

run:
	$(UV) python pac-man.py "$(CONFIG)"

debug:
	$(UV) python -m pdb pac-man.py "$(CONFIG)"

lint:
	$(UV) flake8 .
	$(UV) mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) flake8 .
	$(UV) mypy . --strict --ignore-missing-imports

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find src -type d -name '__pycache__' -prune -exec rm -rf {} +

package:
	$(UV) python package.py

validate: test lint

.PHONY: install run debug test lint lint-strict clean package validate
