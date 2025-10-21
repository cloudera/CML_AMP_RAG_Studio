FROM docker.repository.cloudera.com/cloudera/cdsw/ml-runtime-pbj-jupyterlab-python3.12-standard:2025.01.3-b8

RUN mkdir -p /app
RUN chown -R cdsw:cdsw /app
RUN pip install uv
USER cdsw

COPY ./pyproject.toml /app/
COPY ./uv.lock /app/
WORKDIR /app
RUN uv sync -n -p /usr/local/bin/python3.12

RUN wget https://corretto.aws/downloads/latest/amazon-corretto-21-x64-linux-jdk.tar.gz -O amazon-corretto-21-x64-linux-jdk.tar.gz
COPY --chown=cdsw:cdsw ../prebuilt_artifacts/models/craft_mlt_25k.pth /app/craft_mlt_25k.pth
COPY --chown=cdsw:cdsw ../prebuilt_artifacts/models/latin_g2.pth /app/latin_g2.pth
RUN wget https://github.com/qdrant/qdrant/releases/download/v1.11.3/qdrant-x86_64-unknown-linux-musl.tar.gz -O qdrant.tar.gz

USER root
WORKDIR /tmp
RUN curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

USER cdsw

COPY ./app /app
COPY ./scripts /scripts
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

ENV ML_RUNTIME_EDITION="RAG Studio Runtime" \
       	ML_RUNTIME_SHORT_VERSION="0.1" \
        ML_RUNTIME_MAINTENANCE_VERSION=3 \
        ML_RUNTIME_DESCRIPTION="This runtime includes a virtual environment with the necessary dependencies to run the RAG Studio application."
ENV ML_RUNTIME_FULL_VERSION="${ML_RUNTIME_SHORT_VERSION}.${ML_RUNTIME_MAINTENANCE_VERSION}"
LABEL com.cloudera.ml.runtime.edition=$ML_RUNTIME_EDITION \
        com.cloudera.ml.runtime.full-version=$ML_RUNTIME_FULL_VERSION \
        com.cloudera.ml.runtime.short-version=$ML_RUNTIME_SHORT_VERSION \
        com.cloudera.ml.runtime.maintenance-version=$ML_RUNTIME_MAINTENANCE_VERSION \
        com.cloudera.ml.runtime.description=$ML_RUNTIME_DESCRIPTION