FROM docker-private.infra.cloudera.com/cloudera_base/hardened/cloudera-python:3.10
RUN pip install uv
COPY ./pyproject.toml /app/
COPY ./uv.lock /app/
WORKDIR /app
RUN uv sync

COPY ./app /app
COPY ./scripts /scripts
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

EXPOSE 8081
CMD [ "fastapi", "run", "--host", "0.0.0.0", "--port", "8081" ]
