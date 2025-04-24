import time
start_time = time.time()
"""
RAG app configuration.

All configuration values can be set as environment variables; the variable name is
simply the field name in all capital letters.

"""

# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
# ##############################################################################

import logging
import os.path
from typing import cast, Optional, Literal


SummaryStorageProviderType = Literal["Local", "S3"]


class _Settings:
    """RAG configuration."""

    @property
    def rag_log_level(self) -> int:
        return int(os.environ.get("RAG_LOG_LEVEL", logging.INFO))

    @property
    def rag_databases_dir(self) -> str:
        return os.environ.get("RAG_DATABASES_DIR", os.path.join("..", "databases"))

    @property
    def caii_domain(self) -> str:
        return os.environ["CAII_DOMAIN"]

    @property
    def cdsw_project_id(self) -> str:
        return os.environ["CDSW_PROJECT_ID"]

    @property
    def cdp_token_override(self) -> Optional[str]:
        return os.environ.get("CDP_TOKEN_OVERRIDE")

    @property
    def cdsw_apiv2_key(self) -> Optional[str]:
        return os.environ.get("CDSW_APIV2_KEY")

    @property
    def mlflow_reconciler_data_path(self) -> str:
        return os.environ["MLFLOW_RECONCILER_DATA_PATH"]

    @property
    def qdrant_host(self) -> str:
        return os.environ.get("QDRANT_HOST", "localhost")

    @property
    def qdrant_port(self) -> int:
        return int(os.environ.get("QDRANT_PORT", "6333"))

    @property
    def vector_db_provider(self) -> Optional[str]:
        return os.environ.get("VECTOR_DB_PROVIDER")

    @property
    def opensearch_endpoint(self) -> str:
        return os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")

    @property
    def document_bucket_prefix(self) -> str:
        return os.environ.get("S3_RAG_BUCKET_PREFIX", "")

    @property
    def summary_storage_provider(self) -> SummaryStorageProviderType:
        # TODO: check value of env var, and raise if not SummaryStorageProviderType
        return cast(
            SummaryStorageProviderType,
            os.environ.get("SUMMARY_STORAGE_PROVIDER", "Local"),
        )

    @property
    def document_bucket(self) -> str:
        return os.environ.get("S3_RAG_DOCUMENT_BUCKET", "")

    @property
    def aws_default_region(self) -> Optional[str]:
        return os.environ.get("AWS_DEFAULT_REGION") or None

    def _is_s3_configured(self) -> bool:
        return self.document_bucket != ""

    def is_s3_summary_storage_configured(self) -> bool:
        return self.summary_storage_provider == "S3" and self._is_s3_configured()

    @property
    def azure_openai_api_key(self) -> Optional[str]:
        return os.environ.get("AZURE_OPENAI_API_KEY")


settings = _Settings()

print(f'config.py took {time.time() - start_time:.3f} seconds to import')
