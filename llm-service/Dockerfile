FROM docker-private.infra.cloudera.com/cloudera_base/hardened/cloudera-python:3.10
COPY app/__backup__requirements.txt /app/
WORKDIR /app
RUN pip install -r __backup__requirements.txt

COPY ./app /app
WORKDIR /app

CMD [ "fastapi", "run", "--host", "0.0.0.0" ]
