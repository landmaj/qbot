CMD = . .venv/bin/activate &&

destroy:
	rm -rf .venv
	-docker container stop pg_qbot

venv:
	-python3.8 -m venv .venv
	$(CMD) pip install pip-tools

sync_requirements:
	$(CMD) pip-sync requirements.txt dev-requirements.txt

install:
	$(CMD) pip install -e .[dev]

setup: destroy venv sync_requirements install
	docker run --name pg_qbot --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:11

test:
	$(CMD) alembic upgrade head
	$(CMD) pytest
	$(CMD) alembic downgrade base

compile_requirements:
	$(CMD) pip-compile requirements.in
	$(CMD) pip-compile dev-requirements.in --output-file dev-requirements.txt

run:
	$(CMD) alembic upgrade head
	$(CMD) python run.py --server

format:
	pre-commit run --all-files
