# RAG Studio

### What is Rag Studio?

An AMP that provides a no-code tool to build RAG applications

## Installation

### Important

#### The latest stable version of the AMP lives on the `release/1` branch. The `main` branch is the development branch and may contain unstable code.

Follow the [standard instructions](https://docs.cloudera.com/machine-learning/cloud/applied-ml-prototypes/topics/ml-amp-add-catalog.html) for installing this AMP into your CML workspace.
The "File Name" to use is `catalog-entry.yaml`.

If you do not want to use the catalog-entry, then you should specify the release branch when installing the AMP directly:
- `release/1` is the branch name to use for the latest stable release.

### LLM Model Options

RAG Studio can be used with both Cloudera Inference (CAII) or AWS Bedrock for selecting LLM and embedding models. 

#### Cloudera Inference (CAII) Setup:

To use CAII, you must provide the following environment variables:

- `CAII_DOMAIN` - The domain of the CAII instance

#### AWS Bedrock Setup:

To use AWS Bedrock, you must provide the following environment variables:

- `AWS_DEFAULT_REGION` - defaults to `us-west-2`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Document Storage Options:

RAG Studio can utilize the local file system or an S3 bucket for storing documents. If you are using an S3 bucket, you will need to provide the following environment variables:

- `S3_RAG_BUCKET_PREFIX` - A prefix added to all S3 paths used by Rag Studio
- `S3_RAG_DOCUMENT_BUCKET` - The S3 bucket where uploaded documents are stored

S3 will also require providing the AWS credentials for the bucket.

### Enhanced Parsing Options:

RAG Studio can optionally enable enhanced parsing by providing the `USE_ENHANCED_PDF_PROCESSING` environment variable.  Enabling this will allow RAG Studio to parse images and tables from PDFs.  When enabling this feature, we strongly recommend using this with a GPU and at least 16GB of memory.

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
- Start the Node server (`node index.js`)

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

## The Fine Print

IMPORTANT: Please read the following before proceeding. This AMP includes or otherwise depends on certain third party software packages. Information about such third party software packages are made available in the notice file associated with this AMP. By configuring and launching this AMP, you will cause such third party software packages to be downloaded and installed into your environment, in some instances, from third parties' websites. For each third party software package, please see the notice file and the applicable websites for more information, including the applicable license terms. If you do not wish to download and install the third party software packages, do not configure, launch or otherwise use this AMP. By configuring, launching or otherwise using the AMP, you acknowledge the foregoing statement and agree that Cloudera is not responsible or liable in any way for the third party software packages.
