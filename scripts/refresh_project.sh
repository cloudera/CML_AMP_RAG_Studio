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
nvm use 22
return_code=$?
set -e
if [ $return_code -ne 0 ]; then
    echo "NVM or required Node version not found.  Installing and using..."
    bash scripts/install_node.sh
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

    nvm use 22
fi
cd ui/express
npm install

cd ../../llm-service
pip install uv

uv sync

cd ..
mkdir -p artifacts

RELEASE_URL=https://github.com/cloudera/CML_AMP_RAG_Studio/releases/latest/download
if  [ -n "${RELEASE_TAG}" ] && [ "${RELEASE_TAG}" != "latest" ]; then
    RELEASE_URL=https://github.com/cloudera/CML_AMP_RAG_Studio/releases/download/${RELEASE_TAG}
fi

echo "Downloading release artifacts from ${RELEASE_URL}"
wget "${RELEASE_URL}/rag-api.jar" -O artifacts/rag-api.jar
wget "${RELEASE_URL}/fe-dist.tar.gz" -O artifacts/fe-dist.tar.gz

# unzip the frontend tarball
cd ui
tar -xzf ../artifacts/fe-dist.tar.gz
