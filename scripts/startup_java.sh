#
# CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
# (C) Cloudera, Inc. 2025
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
# Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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

set -ox pipefail

RAG_STUDIO_INSTALL_DIR="/home/cdsw/rag-studio"
if [ -z "$IS_COMPOSABLE" ]; then
  RAG_STUDIO_INSTALL_DIR="/home/cdsw"
fi

if [ -z "$DB_URL" ]; then
  DB_URL_LOCATION="jdbc:h2:file:~/rag-studio/databases/rag"
  if [ -z "$IS_COMPOSABLE" ]; then
    DB_URL_LOCATION="jdbc:h2:file:~/databases/rag"
  fi
  export DB_URL=$DB_URL_LOCATION
fi

for i in {1..3}; do
  echo "Starting Java application..."
  "$JAVA_HOME"/bin/java -jar prebuilt_artifacts/rag-api.jar
  echo "Java application crashed, retrying ($i/3)..."
  sleep 5
done
#while ! curl --output /dev/null --silent --fail http://localhost:8080/api/v1/rag/dataSources; do
#    echo "Waiting for the Java backend to be ready..."
#    sleep 4
#done