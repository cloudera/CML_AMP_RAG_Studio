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

set -eox pipefail

# Array to store background process PIDs
declare -a BACKGROUND_PIDS=()

cleanup() {
    echo "Starting cleanup process..."
    
    # Kill specific background processes we started
    for pid in "${BACKGROUND_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
            # Give it a moment to terminate gracefully
            sleep 2
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    done
    
    # Kill any Java processes running our rag-api.jar
    echo "Killing any remaining Java processes running rag-api.jar..."
    pkill -ef "rag-api.jar" 2>/dev/null || true
    
    # Kill any remaining child processes
    echo "Killing remaining child processes..."
    pkill -eP $$ 2>/dev/null || true
    
    # Kill qdrant processes specifically
    pkill -ef "qdrant/qdrant" 2>/dev/null || true
    
    echo "Cleanup completed."
}

# Function to check if a process is still running
check_process() {
    local pid=$1
    local name=$2
    if kill -0 "$pid" 2>/dev/null; then
        echo "✓ $name (PID: $pid) is running"
        return 0
    else
        echo "✗ $name (PID: $pid) is not running"
        return 1
    fi
}

# Function to verify all services are running
verify_services() {
    echo "Verifying all services are running..."
    local all_running=true
    
    if [[ ${#BACKGROUND_PIDS[@]} -gt 0 ]]; then
        # check_process "${BACKGROUND_PIDS[0]}" "Qdrant" || all_running=false
        # skip checking java because we want to be able to configure the postgres endpoint using the python-provided services, even if java won't start up because it has a bad JDBC URL.
        # check_process "${BACKGROUND_PIDS[1]}" "Java service" || all_running=false
        check_process "${BACKGROUND_PIDS[2]}" "Python backend" || all_running=false
        # if [[ ${#BACKGROUND_PIDS[@]} -gt 3 ]]; then
        #  check_process "${BACKGROUND_PIDS[3]}" "MLflow reconciler" || all_running=false
        # fi
    fi
    
    if [[ "$all_running" == "false" ]]; then
        echo "⚠️  Some services are not running properly!"
        return 1
    else
        echo "✓ All services are running properly"
        return 0
    fi
}

## set the RELEASE_TAG env var from the file, if it exists
source scripts/release_version.txt || true

for sig in INT QUIT HUP TERM; do
  trap "
    cleanup
    trap - $sig EXIT
    kill -s $sig "'"$$"' "$sig"
done
trap cleanup EXIT


export RAG_STUDIO_INSTALL_DIR="/home/cdsw/rag-studio"
if [ -z "$IS_COMPOSABLE" ]; then
  export RAG_STUDIO_INSTALL_DIR="/home/cdsw"
fi

export RAG_DATABASES_DIR=$(pwd)/databases
export LLM_SERVICE_URL="http://localhost:8081"

export MLFLOW_ENABLE_ARTIFACTS_PROGRESS_BAR=false
export MLFLOW_RECONCILER_DATA_PATH=$(pwd)/llm-service/reconciler/data

# start Qdrant vector DB
qdrant/qdrant 2>&1 &
QDRANT_PID=$!
BACKGROUND_PIDS+=($QDRANT_PID)
echo "Started Qdrant with PID: $QDRANT_PID"

# start up the jarva
# grab the most recent java installation and use it for java home
export JAVA_ROOT=`ls -tr ${RAG_STUDIO_INSTALL_DIR}/java-home | tail -1`
export JAVA_HOME="${RAG_STUDIO_INSTALL_DIR}/java-home/${JAVA_ROOT}"

scripts/startup_java.sh 2>&1 &
JAVA_PID=$!
BACKGROUND_PIDS+=($JAVA_PID)
echo "Started Java service with PID: $JAVA_PID"

source scripts/load_nvm.sh > /dev/null

# start Python backend
cd llm-service
mkdir -p $MLFLOW_RECONCILER_DATA_PATH

if [ -e /app/.venv ]; then
  echo "Using existing virtual environment at /app/.venv"
  export UV_PROJECT_ENVIRONMENT=/app/.venv
fi
uv run fastapi run --host 127.0.0.1 --port 8081 2>&1 &

PY_BACKGROUND_PID=$!
BACKGROUND_PIDS+=($PY_BACKGROUND_PID)
echo "Started Python backend with PID: $PY_BACKGROUND_PID"
# wait for the python backend to be ready
echo "Waiting for Python backend to be ready..."
RETRY_COUNT=0
MAX_RETRIES=3000
while ! curl --output /dev/null --silent --fail http://localhost:8081/amp; do
    if ! kill -0 "$PY_BACKGROUND_PID" 2>/dev/null; then
        echo "❌ Python backend process (PID: $PY_BACKGROUND_PID) exited unexpectedly."
        echo "This will trigger cleanup of all services..."
        exit 1
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Python backend failed to start after $MAX_RETRIES attempts ($(($MAX_RETRIES * 4)) seconds)"
        echo "This will trigger cleanup of all services..."
        exit 1
    fi
    
    echo "Waiting for the Python backend to be ready... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 4
done
echo "✓ Python backend is ready and responding"

# start mlflow reconciler
uv run reconciler/mlflow_reconciler.py &
MLFLOW_PID=$!
BACKGROUND_PIDS+=($MLFLOW_PID)
echo "Started MLflow reconciler with PID: $MLFLOW_PID"

# start Node production server

cd ..

cd ui

# Display all tracked background processes
echo "All background processes being tracked:"
for i in "${!BACKGROUND_PIDS[@]}"; do
    echo "  Process $((i+1)): PID ${BACKGROUND_PIDS[i]}"
done

# Verify all services are running before starting Node server
if ! verify_services; then
    echo "❌ Service verification failed. Exiting..."
    exit 1
fi

echo "Starting Node production server (foreground process)..."
# If Node server fails, cleanup will be called due to set -e
node express/dist/index.js
