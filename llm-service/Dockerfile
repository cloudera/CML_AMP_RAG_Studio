FROM docker-private.infra.cloudera.com/cloudera_base/hardened/cloudera-python:3.10
RUN pip install uv
COPY ./pyproject.toml /app/
COPY ./uv.lock /app/
WORKDIR /app
RUN uv install

COPY ./app /app
WORKDIR /app

CMD [ "pdm", "run", "fastapi", "run", "--host", "0.0.0.0" ]
