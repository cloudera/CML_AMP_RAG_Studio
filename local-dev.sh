#
# CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
# (C) Cloudera, Inc. 2024
# All rights reserved.
#
# Applicable Open Source License: Apache 2.0
#
# NOTE: Cloudera open source products are modular software products
# made up of hundreds of individual components, each of which was
# individually copyrighted.  Each Cloudera open source product is a
# collective work under U.S. Copyright Law. Your license to use the
# collective work is as provided in your written agreement with
# Cloudera.  Used apart from the collective work, this file is
# licensed for your use pursuant to the open source license
# identified above.
#
# This code is provided to you pursuant a written agreement with
# (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
# this code. If you do not have a written agreement with Cloudera nor
# with an authorized and properly licensed third party, you do not
# have any rights to access nor to use this code.
#
# Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
# contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
# KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
# WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
# IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
# AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
# ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
# OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
# CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
# RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
# BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
# DATA.
#

set -exo pipefail
set -a && source .env && set +a

export RAG_DATABASES_DIR=$(pwd)/databases
export MLFLOW_RECONCILER_DATA_PATH=$(pwd)/llm-service/reconciler/data

source scripts/release_version.txt || true

cleanup() {
    # kill all processes whose parent is this process
    pkill -P $$
    docker stop qdrant_dev
}

for sig in INT QUIT HUP TERM; do
  trap "
    cleanup
    trap - $sig EXIT
    kill -s $sig "'"$$"' "$sig"
done
trap cleanup EXIT

docker stop qdrant_dev || true

mkdir -p databases
docker run --name qdrant_dev --rm -d -p 6333:6333 -p 6334:6334 -v $(pwd)/databases/qdrant_storage:/qdrant/storage:z qdrant/qdrant

cd llm-service
if [ -z "$USE_SYSTEM_UV" ]; then
  python3.12 -m venv venv
  source venv/bin/activate
  python -m pip install uv
fi
uv sync
#uv run pytest -sxvvra app

uv run mlflow ui &

mkdir -p $MLFLOW_RECONCILER_DATA_PATH
uv run fastapi dev --port=8081 &

# wait for the python backend to be ready
while ! curl --output /dev/null --silent --fail http://localhost:8081/amp; do
    echo "Waiting for the Python backend to be ready..."
    sleep 4
done

# start mlflow reconciler
uv run reconciler/mlflow_reconciler.py &

# start up the jarva
cd ../backend
./gradlew --console=plain bootRun &

# start frontend development server
cd ../ui
pnpm install
pnpm build
pnpm dev &

# start the proxy
cd express
pnpm run dev
