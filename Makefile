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

test:
	$(UV) python -m unittest discover -s tests -v

lint:
	$(UV) flake8 .
	$(UV) mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) flake8 .
	$(UV) mypy . --strict --ignore-missing-imports

clean:
	$(UV) python clean.py

package:
	$(UV) python package.py

validate: test lint

.PHONY: install run debug test lint lint-strict clean package validate
