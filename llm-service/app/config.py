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
from enum import Enum
from typing import cast, Optional, Literal

from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE


logger = logging.getLogger(__name__)


SummaryStorageProviderType = Literal["Local", "S3"]
ChatStoreProviderType = Literal["Local", "S3"]
VectorDbProviderType = Literal["QDRANT", "OPENSEARCH", "CHROMADB"]
MetadataDbProviderType = Literal["H2", "PostgreSQL"]


class ModelSource(str, Enum):
    AZURE = "Azure"
    OPENAI = "OpenAI"
    BEDROCK = "Bedrock"
    CAII = "CAII"


class _Settings:
    """RAG configuration."""

    @property
    def metadata_api_url(self) -> str:
        return os.environ.get("API_URL", "http://localhost:8080")

    @property
    def rag_log_level(self) -> int:
        return int(os.environ.get("RAG_LOG_LEVEL", logging.INFO))

    @property
    def rag_databases_dir(self) -> str:
        return os.environ.get("RAG_DATABASES_DIR", os.path.join("..", "databases"))

    @property
    def tools_dir(self) -> str:
        return os.path.join("..", "tools")

    @property
    def caii_domain(self) -> Optional[str]:
        return os.environ.get("CAII_DOMAIN")

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
    def qdrant_timeout(self) -> int:
        return int(os.environ.get("QDRANT_TIMEOUT", "300"))

    @property
    def qdrant_grpc_port(self) -> int:
        port = os.environ.get("QDRANT_GRPC_PORT", "6334")
        return int(port)

    @property
    def advanced_pdf_parsing(self) -> bool:
        return os.environ.get("USE_ENHANCED_PDF_PROCESSING", "false").lower() == "true"

    @property
    def vector_db_provider(self) -> Optional[str]:
        return os.environ.get("VECTOR_DB_PROVIDER")

    @property
    def opensearch_endpoint(self) -> str:
        return os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")

    @property
    def opensearch_namespace(self) -> str:
        return os.environ.get("OPENSEARCH_NAMESPACE") or "rag_document_index"

    @property
    def opensearch_username(self) -> str:
        return os.environ.get("OPENSEARCH_USERNAME", "")

    @property
    def opensearch_password(self) -> str:
        return os.environ.get("OPENSEARCH_PASSWORD", "")

    @property
    def chromadb_host(self) -> str:
        return os.environ.get("CHROMADB_HOST", "localhost")

    @property
    def chromadb_port(self) -> int | None:
        value = os.environ.get("CHROMADB_PORT")
        if value is None or value == "":
            return None
        try:
            return int(value)
        except ValueError:
            logger.exception(
                'Failed to parse CHROMADB_PORT "%s" as int',
                value,
            )
            return None

    @property
    def chromadb_token(self) -> str:
        return os.environ.get("CHROMADB_TOKEN", "")

    @property
    def chromadb_tenant(self) -> str:
        return os.environ.get("CHROMADB_TENANT") or DEFAULT_TENANT

    @property
    def chromadb_database(self) -> str:
        return os.environ.get("CHROMADB_DATABASE") or DEFAULT_DATABASE

    @property
    def chromadb_server_ssl_cert_path(self) -> str | None:
        return os.environ.get("CHROMADB_SERVER_SSL_CERT_PATH")

    @property
    def chromadb_enable_anonymized_telemetry(self) -> bool:
        return (
            os.environ.get("CHROMADB_ENABLE_ANONYMIZED_TELEMETRY", "false").lower()
            == "true"
        )

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
    def chat_store_provider(self) -> ChatStoreProviderType:
        # TODO: check value of env var, and raise if not ChatStoreProviderType
        return cast(
            ChatStoreProviderType,
            os.environ.get("CHAT_STORE_PROVIDER", "Local"),
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

    def is_s3_chat_store_configured(self) -> bool:
        return self.chat_store_provider == "S3" and self._is_s3_configured()

    @property
    def azure_openai_api_key(self) -> Optional[str]:
        return os.environ.get("AZURE_OPENAI_API_KEY")

    @property
    def azure_openai_endpoint(self) -> Optional[str]:
        return os.environ.get("AZURE_OPENAI_ENDPOINT")

    @property
    def azure_openai_api_version(self) -> Optional[str]:
        return os.environ.get("AZURE_OPENAI_API_VERSION")

    @property
    def openai_api_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")

    @property
    def openai_api_base(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_BASE")

    @property
    def model_provider(self) -> Optional[ModelSource]:
        """The preferred model provider to use.
        Options: 'AZURE', 'CAII', 'OPENAI', 'BEDROCK'
        If not set, will use the first available provider in priority order."""
        provider = os.environ.get("MODEL_PROVIDER")
        if provider is None:
            return None
        try:
            return ModelSource(provider)
        except ValueError:
            logger.exception(
                'Invalid MODEL_PROVIDER "%s"',
                provider,
            )
            return None


settings = _Settings()
