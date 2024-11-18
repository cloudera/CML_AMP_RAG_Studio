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
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class OTelSettings(BaseSettings, str_strip_whitespace=True):
    """
    OpenTelemetry configuration.

    Environment variable names are taken from the OTel spec. This exists to enforce
    values we require and set our own defaults; otherwise OTel will use its defaults
    which could error at runtime.

    """

    model_config = SettingsConfigDict(env_prefix="otel_")

    service_name: str = "llm-service"
    exporter_otlp_endpoint: Optional[str] = None


class PGVectorStoreSettings(BaseSettings, str_strip_whitespace=True):
    """Postgres vector store configuration."""

    db_url: str = "postgresql://postgres:password@localhost:5432"
    db_name: str = "vector_db"


class PrometheusSettings(BaseSettings, str_strip_whitespace=True):
    """Prometheus client configuration."""

    model_config = SettingsConfigDict(env_prefix="prometheus_")

    port: int = 9464


class S3Settings(BaseSettings, str_strip_whitespace=True):
    """S3 configuration."""

    endpoint_url: str = "http://s3:9090"


class Settings(BaseSettings):
    """RAG configuration."""

    otel: OTelSettings = OTelSettings()
    pgvector: PGVectorStoreSettings = PGVectorStoreSettings()
    prometheus: PrometheusSettings = PrometheusSettings()
    s3: S3Settings = S3Settings()

    rag_log_level: int = logging.INFO
    rag_databases_dir: str = os.path.join("..", "databases")


settings = Settings()
