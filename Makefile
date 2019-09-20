setup:
	python3.7 -m venv .venv
	.venv/bin/python -m pip install -e .[dev]
	.venv/bin/python -m alembic upgrade head
	docker run --name pg_qbot --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:11
	.venv/bin/python -m alembic downgrade base

destroy:
	rm -rf .venv
	docker container stop pg_qbot

test:
	.venv/bin/python -m pytest
