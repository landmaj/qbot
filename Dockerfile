FROM python:3.8-alpine as build

RUN apk update && apk add --virtual .build-deps --no-cache \
	build-base \
	gcc \
	libxml2-dev \
	libxslt-dev \
	musl-dev \
	postgresql-dev

RUN pip install pip==20.0.2 && \
    pip install wheel==0.35.1 && \
    pip install pip-tools==5.1.0

COPY requirements.txt src/
RUN mkdir /wheel && pip wheel -w /wheel -r /src/requirements.txt

COPY [ \
    "*requirements.txt", \
    "alembic.ini", \
    "setup.py", \
    "src/" \
]
COPY qbot src/qbot
COPY vendor src/vendor
COPY migrations src/migrations

RUN pip wheel --no-index --find-links /wheel -w /wheel /src


FROM python:3.8-alpine as prod

RUN apk update && apk add libxslt
COPY --from=build /wheel /wheel

RUN pip install --no-cache-dir --no-index --find-links /wheel qbot
RUN rm -rf /wheel

ENTRYPOINT ["qbot"]
