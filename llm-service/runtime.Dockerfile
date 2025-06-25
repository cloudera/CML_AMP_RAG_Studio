FROM docker.repository.cloudera.com/cloudera/cdsw/ml-runtime-pbj-jupyterlab-python3.12-standard:2025.01.3-b8

RUN mkdir -p /app
RUN chown -R cdsw:cdsw /app
RUN pip install uv
USER cdsw

COPY ./pyproject.toml /app/
COPY ./uv.lock /app/
WORKDIR /app
RUN uv sync -n -p /usr/local/bin/python3.12

COPY ./app /app
COPY ./scripts /scripts
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

ENV ML_RUNTIME_EDITION="RAG Studio Runtime" \
       	ML_RUNTIME_SHORT_VERSION="0.1" \
        ML_RUNTIME_MAINTENANCE_VERSION=2 \
        ML_RUNTIME_DESCRIPTION="This runtime includes a virtual environment with the necessary dependencies to run the RAG Studio application."
ENV ML_RUNTIME_FULL_VERSION="${ML_RUNTIME_SHORT_VERSION}.${ML_RUNTIME_MAINTENANCE_VERSION}"
LABEL com.cloudera.ml.runtime.edition=$ML_RUNTIME_EDITION \
        com.cloudera.ml.runtime.full-version=$ML_RUNTIME_FULL_VERSION \
        com.cloudera.ml.runtime.short-version=$ML_RUNTIME_SHORT_VERSION \
        com.cloudera.ml.runtime.maintenance-version=$ML_RUNTIME_MAINTENANCE_VERSION \
        com.cloudera.ml.runtime.description=$ML_RUNTIME_DESCRIPTION