# RAG Studio

### What is Rag Studio?

An AMP that provides a no-code tool to build RAG applications

## Documentation

- UI Guide: [docs/rag-studio-ui-guide.md](docs/rag-studio-ui-guide.md)
- Quickstart: [docs/rag-studio-quickstart.md](docs/rag-studio-quickstart.md)

## Installation

### Important

#### The latest stable version of the AMP lives on the `release/1` branch. The `main` branch is the development branch and may contain unstable code.

Follow the [standard instructions](https://docs.cloudera.com/machine-learning/cloud/applied-ml-prototypes/topics/ml-amp-add-catalog.html) for installing this AMP into your CML workspace.
The "File Name" to use is `catalog-entry.yaml`.

If you do not want to use the catalog-entry, then you should specify the release branch when installing the AMP directly:

- `release/1` is the branch name to use for the latest stable release.

### LLM Model Options

RAG Studio can be used with Cloudera AI Inference (CAII), AWS Bedrock, or Azure OpenAI for selecting LLM and embedding models.

#### Cloudera AI Inference (CAII) Setup:

To use CAII, you must provide the following environment variables:

- `CAII_DOMAIN` - The domain of the Cloudera AI Inference instance

#### AWS Bedrock Setup:

To use AWS Bedrock, you must provide the following environment variables:

- `AWS_DEFAULT_REGION` - defaults to `us-west-2`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### Azure OpenAI Setup:

To use Azure OpenAI, you must provide the following environment variables:

- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI service endpoint URL
- `OPENAI_API_VERSION` - The Azure OpenAI API version to use

### Document Storage Options:

RAG Studio can utilize the local file system or an S3 bucket for storing documents. If you are using an S3 bucket, you will need to provide the following environment variables:

- `S3_RAG_BUCKET_PREFIX` - A prefix added to all S3 paths used by Rag Studio
- `S3_RAG_DOCUMENT_BUCKET` - The S3 bucket where uploaded documents are stored

S3 will also require providing the AWS credentials for the bucket.

### Vector Database Options

RAG Studio supports Qdrant (default), OpenSearch (Cloudera Semantic Search), and ChromaDB.

- To choose the vector DB, set `VECTOR_DB_PROVIDER` to one of `QDRANT`, `OPENSEARCH`, or `CHROMADB` in your `.env`.

#### ChromaDB Setup

If you select ChromaDB, configure the following environment variables in `.env`:

- `CHROMADB_HOST` - Hostname or URL for ChromaDB. Use `localhost` for local Docker.
- `CHROMADB_PORT` - Port for ChromaDB (default `8000`). Not required if `CHROMADB_HOST` starts with `https://` and the server infers the port.
- `CHROMADB_TENANT` - Optional. Defaults to the Chroma default tenant.
- `CHROMADB_DATABASE` - Optional. Defaults to the Chroma default database.
- `CHROMADB_TOKEN` - Optional. Include if your Chroma server requires an auth token.
- `CHROMADB_SERVER_SSL_CERT_PATH` - Optional. Path to PEM bundle for TLS verification when using HTTPS with a private CA.
- `CHROMADB_ENABLE_ANONYMIZED_TELEMETRY` - Optional. Enables anonymized telemetry in the ChromaDB client; defaults to `false`.

Notes:

- The local-dev script will automatically start a ChromaDB Docker container when `VECTOR_DB_PROVIDER=CHROMADB`, `CHROMADB_HOST=localhost` on `CHROMADB_PORT=8000`.
- ChromaDB collections are automatically namespaced using the tenant and database values to avoid conflicts between different RAG Studio instances.
- For production deployments, consider using a dedicated ChromaDB server with authentication enabled via `CHROMADB_TOKEN`.
- When using HTTPS endpoints, ensure your certificate chain is properly configured or provide the CA bundle path via `CHROMADB_SERVER_SSL_CERT_PATH`.
- Anonymized telemetry is disabled by default. You can enable it either by setting `CHROMADB_ENABLE_ANONYMIZED_TELEMETRY=true`.

### Enhanced Parsing Options:

RAG Studio can optionally enable enhanced parsing by providing the `USE_ENHANCED_PDF_PROCESSING` environment variable. Enabling this will allow RAG Studio to parse images and tables from PDFs. When enabling this feature, we strongly recommend using this with a GPU and at least 16GB of memory.

### Cloudera DataFlow (Nifi) Setup:

Rag Studio provides a Nifi template that can be downloaded for a given Knowledge Base from the `Connections` tab.
The Nifi template can then be imported into your Cloudera DataFlow (CDF) environment and used to setup a pipeline into Rag Studio.

IMPORTANT: In order to inject data from CDF, users must disable authentication of the AMP Project from their Cloudera Machine Learning (CML) workspace.
This carries a security risk and should be carefully considered before proceeding.

### Updating RAG Studio

The Rag Studio UI will show a banner at the top of the page when a new version of the AMP is available.
To update the Rag Studio, click on the banner and follow the instructions. If any issues are encountered, please contact
Cloudera for assistance. Additionally, further details on the AMP status can be found from the CML workspace.

### Common Issues

- TBD

## CDP Token Override

If you are using Cloudera AI Inference and would like to override the default CDP token used within RAG Studio, you can do so by providing the `CDP_TOKEN_OVERRIDE` environment variable.
This variable can be set from the project settings for the AMP in CML.

## Air-gapped Environments

If you are using an air-gapped environment, you will need to whitelist at the minimum the following domains in order to use the AMP.
There may be other domains that need to be whitelisted depending on your environment and the model service provider you select.

- `https://github.com`
- `https://raw.githubusercontent.com`
- `https://pypi.org`
- `https://files.pythonhosted.org`
- `http://registry.npmjs.org/`
- `http://services.gradle.org`
- `https://corretto.aws/downloads/latest/`

## Developer Information

Ignore this section unless you are working on developing or enhancing this AMP.

### Environment Variables

Make a copy of the `.env.example` file and rename it to `.env`. Fill in the values for the environment variables.

### Upgrading EasyOCR Model Artifacts

We store EasyOCR model artifacts in a placeholder Github Release located [here](https://github.com/cloudera/CML_AMP_RAG_Studio/releases/tag/model_download) to facilitate faster downloads.
To upgrade the EasyOCR model artifacts, download the latest model artifacts from the EasyOCR repository and upload them to a Github Release.

### Local Development

Every service can be started locally for development by running `./local-dev.sh`. Once started, the UI can be accessed
at `http://localhost:5173`. Additionally, each service can be started individually by following the instructions below.

#### FE Setup

- Navigate to the FE subdirectory (`cd ./ui`)
- Make sure node is installed (if not, run `brew install node@22`)
- Run `pnpm install` (if pnpm is not installed on your system, install globally `brew install pnpm`)
- Start the dev server (`pnpm dev`) [if you want to run the dev server standalone, for debugging, for instance?]

#### Node Setup

The Node Service is used as a proxy and to serve static assets. For local development, the proxying and static
asset serving is handled by the FE service. The Node service is only used in production. However, if you want to run
the Node service locally, you can do so by following these steps:

- Build the FE service (`cd ./ui` and then `pnpm build`)
- Navigate to the Node subdirectory (`cd ./express`)
- Run `pnpm install` (if pnpm is not installed on your system, install globally `brew install pnpm`)
- Start the Node server (`pnpm run start`)

#### Python Setup

- Install Python 3.10 (via [pyenv](https://github.com/pyenv/pyenv), probably) (directly via brew, if you must)
- `cd llm-service`
- Install `uv`.
  - We recommend installing via `brew install uv`, but you can also install it directly in your python environment if you prefer.
- `uv sync` - this creates a `uv` virtual environment in `.venv` and installs the dependencies
- `uv fastapi dev`
  - the python-based service ends up running on port 8000

#### Java Setup

- Install Java 21 and make default JDK
- `cd ./backend`
- `./gradlew bootRun`

#### To run quadrant locally

```
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/databases/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

#### To run ChromaDB locally

```
docker run --name chromadb_dev --rm -d -p 8000:8000 -v $(pwd)/databases/chromadb_storage:/data chromadb/chroma
```

#### Use ChromaDB with local-dev.sh

- Copy `.env.example` to `.env`.
- Set `VECTOR_DB_PROVIDER=CHROMADB` in `.env` (defaults assume `CHROMADB_HOST=localhost` and `CHROMADB_PORT=8000`).
- Run `./local-dev.sh` from the repo root. When `CHROMADB_HOST=localhost`, the script will auto-start a ChromaDB Docker container.

#### Modifying UI in CML

- This is an unsupported workflow, but it is possible to modify the UI code in CML.

* Start a CML Session from a CML Project that has the RAG Studio AMP installed.
* Open the terminal in the CML Session and navigate to the `ui` directory.
* Run `source ~/.bashrc` to ensure the Node environment variables are loaded.
* Install PNPM using `npm install -g pnpm`. Docs on PNPM can be found here: https://pnpm.io/installation#using-npm
* Run `pnpm install` to install the dependencies.
* Make your changes to the UI code in the `ui` directory.
* Run `pnpm build` to build the new UI bundle.

## The Fine Print

IMPORTANT: Please read the following before proceeding. This AMP includes or otherwise depends on certain third party software packages. Information about such third party software packages are made available in the notice file associated with this AMP. By configuring and launching this AMP, you will cause such third party software packages to be downloaded and installed into your environment, in some instances, from third parties' websites. For each third party software package, please see the notice file and the applicable websites for more information, including the applicable license terms. If you do not wish to download and install the third party software packages, do not configure, launch or otherwise use this AMP. By configuring, launching or otherwise using the AMP, you acknowledge the foregoing statement and agree that Cloudera is not responsible or liable in any way for the third party software packages.
