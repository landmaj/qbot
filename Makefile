CMD = . .venv/bin/activate &&

destroy:
	rm -rf .venv
	-docker container stop pg_qbot

venv:
	-python3.8 -m venv .venv
	$(CMD) pip install pip==20.0.2
	$(CMD) pip install pip-tools==5.1.0

install:
	$(CMD) pip-sync requirements.txt dev-requirements.txt
	$(CMD) pip install -e .[dev]

db:
	-docker run --name pg_qbot --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:11
	sleep 2
	$(CMD) alembic upgrade head

setup: venv install db

test:
	$(CMD) alembic downgrade base
	$(CMD) alembic upgrade head
	$(CMD) pytest

run-webapp:
	$(CMD) python qbot/run.py --server

run-scheduler:
	$(CMD) python qbot/run.py --scheduler

format:
	pre-commit run --all-files

compile_requirements:
	$(CMD) pip-compile requirements.in
	$(CMD) pip-compile dev-requirements.in --output-file dev-requirements.txt

msg = $(error USAGE: make migration msg="commit message")
migration:
	$(CMD) alembic revision --autogenerate -m "$(msg)"

build_image:
	docker build . -t landmaj/qbot
push_image:
	docker push landmaj/qbot:latest
