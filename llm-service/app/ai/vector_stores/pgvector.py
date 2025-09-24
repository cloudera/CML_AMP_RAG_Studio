#
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
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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
#

import functools
import json
import logging
from typing import Optional, cast

import fastapi.exceptions
import psycopg2
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.indices import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore as LlamaIndexPGVectorStore
from psycopg2.extras import RealDictCursor

from app.config import settings
from app.services import models
from app.services.metadata_apis import data_sources_metadata_api
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


def _new_pg_connection() -> psycopg2.extensions.connection:
    try:
        conn = psycopg2.connect(
            host=settings.pgvector_host,
            port=settings.pgvector_port,
            dbname=settings.pgvector_db,
            user=settings.pgvector_user,
            password=settings.pgvector_password,
            cursor_factory=RealDictCursor,
        )
        return conn
    except Exception as e:
        logger.error("Error connecting to PostgreSQL: %s", e)
        raise e


class PgVectorStore(VectorStore):
    # https://github.com/run-llama/llama_index/blob/v0.14.2/llama-index-integrations/vector_stores/llama-index-vector-stores-postgres/llama_index/vector_stores/postgres/base.py#L123
    _LLAMA_INDEX_TABLE_NAME_PREFIX = "data_"

    @staticmethod
    def for_chunks(
        data_source_id: int,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> "PgVectorStore":
        return PgVectorStore(
            table_name=f"index_{data_source_id}",
            data_source_id=data_source_id,
            conn=conn,
        )

    @staticmethod
    def for_summaries(
        data_source_id: int,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> "PgVectorStore":
        return PgVectorStore(
            table_name=f"summary_index_{data_source_id}",
            data_source_id=data_source_id,
            conn=conn,
        )

    def __init__(
        self,
        table_name: str,
        data_source_id: int,
        conn: Optional[psycopg2.extensions.connection] = None,
    ):
        self.conn = conn or _new_pg_connection()
        if table_name.startswith(self._LLAMA_INDEX_TABLE_NAME_PREFIX):
            self.table_name = table_name
        else:
            self.table_name = self._LLAMA_INDEX_TABLE_NAME_PREFIX + table_name
        self.data_source_id = data_source_id

    def get_embedding_model(self) -> BaseEmbedding:
        data_source_metadata = data_sources_metadata_api.get_metadata(
            self.data_source_id
        )
        return models.Embedding.get(data_source_metadata.embedding_model)

    def size(self) -> Optional[int]:
        if not self.exists():
            return None
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) as count FROM {self.table_name}")
                return cast(int, cur.fetchone()["count"])
        except Exception as e:
            logger.warning("Error getting size of table %s: %s", self.table_name, e)
            return None

    def delete(self) -> None:
        if not self.exists():
            return None
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name} CASCADE")
            self.conn.commit()
        except Exception as e:
            logger.error("Error deleting table %s: %s", self.table_name, e)
            raise fastapi.exceptions.HTTPException(
                status_code=500,
                detail=f"Error deleting table {self.table_name}: {e}",
            ) from e

    def delete_document(self, document_id: str) -> None:
        if not self.exists():
            return None
        try:
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.llama_vector_store(),
                embed_model=models.Embedding.get_noop(),
            )
            index.delete_ref_doc(document_id)
        except Exception as e:
            logger.error(
                "Error deleting document %s from table %s: %s",
                document_id,
                self.table_name,
                e,
            )
            raise fastapi.exceptions.HTTPException(
                status_code=500,
                detail=f"Error deleting document {document_id} from table {self.table_name}: {e}",
            ) from e

    def exists(self) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_name = %s
                    """,
                    (self.table_name,),
                )
                return cast(int, cur.fetchone()["count"]) > 0
        except Exception as e:
            logger.warning("Error checking if table %s exists: %s", self.table_name, e)
            return False

    @staticmethod
    @functools.cache
    def _find_dim(data_source_id: int) -> int:
        datasource_metadata = data_sources_metadata_api.get_metadata(data_source_id)
        embedding_model = models.Embedding.get(datasource_metadata.embedding_model)
        vector = embedding_model.get_query_embedding("any")
        return len(vector)

    def llama_vector_store(self) -> LlamaIndexPGVectorStore:
        return LlamaIndexPGVectorStore.from_params(
            host=settings.pgvector_host,
            port=settings.pgvector_port,
            database=settings.pgvector_db,
            user=settings.pgvector_user,
            password=settings.pgvector_password,
            table_name=self.table_name.removeprefix(
                self._LLAMA_INDEX_TABLE_NAME_PREFIX,
            ),
            embed_dim=self._find_dim(self.data_source_id),
        )

    def visualize(
        self, user_query: Optional[str] = None
    ) -> list[tuple[tuple[float, float], str]]:
        if not self.exists():
            return []

        embeddings: list[list[float]] = []
        filenames: list[str] = []

        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT embedding, metadata_->>'file_name' as file_name FROM {self.table_name} LIMIT 5000"
            )
            rows = cur.fetchall()
            for row in rows:
                if row["file_name"] and row["embedding"]:
                    filenames.append(row["file_name"])
                    embedding = row["embedding"]
                    if isinstance(embedding, str):
                        embedding = json.loads(embedding)
                    if isinstance(embedding, list):
                        embeddings.append(cast(list[float], embedding))

        return self.visualize_embeddings(embeddings, filenames, user_query)
