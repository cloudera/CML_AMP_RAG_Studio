#!/usr/bin/bash
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

## set the RELEASE_TAG env var from the file, if it exists
source scripts/release_version.txt || true


set +e
source scripts/load_nvm.sh > /dev/null

# Need to install node for legacy installations before node was used
nvm use 22
return_code=$?
set -e
if [ $return_code -ne 0 ]; then
    echo "NVM or required Node version not found.  Installing and using..."
    bash scripts/install_node.sh
    source scripts/load_nvm.sh > /dev/null

    nvm use 22
fi

cd llm-service

set +e
uv --version
return_code=$?
set -e
if [ $return_code -ne 0 ]; then
  pip install uv
fi

if [ -e /app/.venv ]; then
  echo "Using existing virtual environment at /app/.venv"
  export UV_PROJECT_ENVIRONMENT=/app/.venv
fi
uv sync --no-dev

echo "Unzipping prebuilt artifacts..."
cd ..
# unzip the frontend tarball
cd ui
rm -rf dist
tar -xzf ../prebuilt_artifacts/fe-dist.tar.gz

cd express
rm -rf node_modules
tar -xzf ../../prebuilt_artifacts/node-dist.tar.gz

cd ../../scripts
