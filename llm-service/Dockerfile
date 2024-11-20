FROM docker-private.infra.cloudera.com/cloudera_base/hardened/cloudera-python:3.10
RUN pip install pdm
COPY ./pyproject.toml /app/
COPY ./pdm.lock /app/
WORKDIR /app
RUN pdm install

COPY ./app /app
WORKDIR /app

CMD [ "pdm", "run", "fastapi", "run", "--host", "0.0.0.0" ]
