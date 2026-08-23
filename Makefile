DEF_CONFIG = config.json

run:
	uv run python3 -m src DEF_CONFIG

install:
	uv sync

lint:
	flake8 --exclude=.venv .
	mypy --exclude="^.venv/" . \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	flake8 --exclude=.venv,data .
	mypy --exclude="^.venv/|data/" . --strict

debug:
	uv run python3 -m pdb src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

prompt:
	cat src/*.py > prompt.txt
	cat src/screens/*.py >> prompt
	cat src/mlx_wrapper/*.py >> prompt
	echo "\nStructure:\n" | cat  >> prompt.txt
	ls -R src >> prompt.txt
	xclip -selection clipboard < prompt.txt

.PHONY: run install lint lint-strict debug clean prompt prompt_mlx
