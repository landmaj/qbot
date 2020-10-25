FROM python:3.8-alpine as build

RUN apk update && apk add --no-cache \
	build-base \
	gcc \
	libxml2-dev \
	libxslt-dev \
	musl-dev \
	postgresql-dev

RUN python3 -m venv .venv && \
    .venv/bin/pip install pip==20.0.2 && \
    .venv/bin/pip install pip-tools==5.1.0

COPY requirements.txt src/
RUN .venv/bin/pip-sync src/requirements.txt

COPY [ \
    "*requirements.txt", \
    "alembic.ini", \
    "setup.py", \
    "migrations", \
    "qbot", \
    "vendor", \
    "src/" \
]
RUN .venv/bin/pip install /src


FROM python:3.8-alpine as prod

RUN apk update && apk add \
    libxslt
COPY --from=build .venv .venv

ENTRYPOINT [".venv/bin/qbot"]
