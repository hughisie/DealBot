.PHONY: setup run test lint package clean

setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e ".[dev]"

run:
	./venv/bin/python -m adp.app

test:
	./venv/bin/pytest

lint:
	./venv/bin/ruff check adp tests
	./venv/bin/mypy adp

format:
	./venv/bin/black adp tests
	./venv/bin/ruff check --fix adp tests

package:
	./venv/bin/briefcase build
	./venv/bin/briefcase package

clean:
	rm -rf build dist *.egg-info venv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
