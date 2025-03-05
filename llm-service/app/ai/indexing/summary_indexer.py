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

import logging
import os
import shutil
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, cast, List

from llama_index.core import (
    DocumentSummaryIndex,
    StorageContext,
    get_response_synthesizer,
    load_index_from_storage, PromptHelper,
)
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.schema import (
    Document,
    NodeRelationship,
    TextNode,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from app.services import models
from .base import BaseTextIndexer
from .readers.base_reader import ReaderConfig, ChunksResult
from ..vector_stores.qdrant import QdrantVectorStore
from ...config import Settings
from ...services.models import CAIIModelProvider

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = "Summarize the contents into less than 100 words."

# Since we don't use anything fancy to store the summaries, it's possible that two threads
# try to do a write operation at the same time and we end up with a race condition.
# Basically filesystems aren't ACID, so don't pretend that they are.
# We could have a lock per data source, but this is simpler.
_write_lock = Lock()


class SummaryIndexer(BaseTextIndexer):
    def __init__(
        self,
        data_source_id: int,
        splitter: SentenceSplitter,
        llm: LLM,
        embedding_model: BaseEmbedding,
        reader_config: Optional[ReaderConfig] = None,
    ):
        super().__init__(data_source_id, reader_config=reader_config)
        self.splitter = splitter
        self.llm = llm
        self.embedding_model = embedding_model

    @staticmethod
    def __database_dir(data_source_id: int) -> str:
        return os.path.join(
            Settings().rag_databases_dir, f"doc_summary_index_{data_source_id}"
        )

    def __persist_dir(self) -> str:
        return SummaryIndexer.__database_dir(self.data_source_id)

    @staticmethod
    def __persist_root_dir() -> str:
        return os.path.join(Settings().rag_databases_dir, "doc_summary_index_global")

    def __index_kwargs(self, embed_summaries: bool = True) -> Dict[str, Any]:
        return SummaryIndexer.__index_configuration(
            self.llm, self.embedding_model, self.data_source_id, embed_summaries
        )

    @staticmethod
    def __index_configuration(
        llm: LLM,
        embedding_model: BaseEmbedding,
        data_source_id: int,
        embed_summaries: bool = True,
    ) -> Dict[str, Any]:
        prompt_helper: Optional[PromptHelper] = None
        # if we're using CAII, let's be conservative, and use a small context window to account for mistral's small context
        if CAIIModelProvider.is_enabled():
            prompt_helper=PromptHelper(context_window=3000)
        return {
            "llm": llm,
            "response_synthesizer": get_response_synthesizer(
                response_mode=ResponseMode.TREE_SUMMARIZE,
                llm=llm,
                use_async=True,
                verbose=True,
                prompt_helper=prompt_helper
            ),
            "show_progress": True,
            "embed_model": embedding_model,
            "embed_summaries": embed_summaries,
            "summary_query": SUMMARY_PROMPT,
            "data_source_id": data_source_id,
        }

    def __init_summary_store(self, persist_dir: str) -> DocumentSummaryIndex:
        doc_summary_index = DocumentSummaryIndex.from_documents(
            [],
            **self.__index_kwargs(),
        )
        doc_summary_index.storage_context.persist(persist_dir=persist_dir)
        return doc_summary_index

    def __summary_indexer(
        self, persist_dir: str, embed_summaries: bool = True
    ) -> DocumentSummaryIndex:
        try:
            return SummaryIndexer.__summary_indexer_with_config(
                persist_dir=persist_dir,
                index_configuration=self.__index_kwargs(embed_summaries),
            )
        except FileNotFoundError:
            doc_summary_index = self.__init_summary_store(persist_dir)
            return doc_summary_index

    @staticmethod
    def __summary_indexer_with_config(
        persist_dir: str, index_configuration: Dict[str, Any]
    ) -> DocumentSummaryIndex:
        data_source_id: int = index_configuration.get("data_source_id")
        storage_context = StorageContext.from_defaults(
            persist_dir=persist_dir,
            vector_store=QdrantVectorStore.for_summaries(
                data_source_id
            ).llama_vector_store(),
        )
        doc_summary_index: DocumentSummaryIndex = cast(
            DocumentSummaryIndex,
            load_index_from_storage(
                storage_context=storage_context,
                **index_configuration,
            ),
        )
        return doc_summary_index

    def index_file(self, file_path: Path, document_id: str) -> None:
        logger.debug(f"Creating summary for file {file_path}")

        reader_cls = self._get_reader_class(file_path)

        reader = reader_cls(
            splitter=self.splitter,
            document_id=document_id,
            data_source_id=self.data_source_id,
            config=self.reader_config,
        )

        logger.debug(f"Parsing file: {file_path}")

        chunks: ChunksResult = reader.load_chunks(file_path)
        nodes: List[TextNode] = chunks.chunks

        if not nodes:
            logger.warning(f"No chunks found for file {file_path}")
            return

        with _write_lock:
            persist_dir = self.__persist_dir()
            summary_store: DocumentSummaryIndex = self.__summary_indexer(persist_dir)
            summary_store.insert_nodes(nodes)
            summary_store.storage_context.persist(persist_dir=persist_dir)

            self.__update_global_summary_store(summary_store, added_node_id=document_id)

        logger.debug(f"Summary for file {file_path} created")

    def __update_global_summary_store(
        self,
        summary_store: DocumentSummaryIndex,
        added_node_id: Optional[str] = None,
        deleted_node_id: Optional[str] = None,
    ) -> None:
        # Llama index doesn't seem to support updating the summary when we add more documents.
        # So what we do instead is re-load all the summaries for the documents already associated with the data source
        # and re-index it with the addition/removal.
        global_persist_dir = self.__persist_root_dir()
        global_summary_store = self.__summary_indexer(
            global_persist_dir, embed_summaries=False
        )
        data_source_node = Document(doc_id=str(self.data_source_id))

        summary_id = global_summary_store.index_struct.doc_id_to_summary_id.get(
            str(self.data_source_id)
        )

        new_nodes = []
        if summary_id:
            document_ids = global_summary_store.index_struct.summary_id_to_node_ids.get(
                summary_id
            )
            if document_ids:
                # Reload the summary for each existing node id, which correspond to full documents
                summaries = [
                    summary_store.get_document_summary(document_id)
                    for document_id in document_ids
                ]

                new_nodes = [
                    Document(
                        doc_id=document_id,
                        text=document_summary,
                        relationships={
                            NodeRelationship.SOURCE: data_source_node.as_related_node_info()
                        },
                    )
                    for document_id, document_summary in zip(document_ids, summaries)
                ]

        if added_node_id:
            new_nodes.append(
                Document(
                    doc_id=added_node_id,
                    text=summary_store.get_document_summary(added_node_id),
                    relationships={
                        NodeRelationship.SOURCE: data_source_node.as_related_node_info()
                    },
                )
            )

        if deleted_node_id:
            new_nodes = [node for node in new_nodes if node.id_ != deleted_node_id]

        # Delete first so that we don't accumulate trash in the summary store.
        try:
            global_summary_store.delete_ref_doc(
                str(self.data_source_id), delete_from_docstore=True
            )
        except (KeyError, UnexpectedResponse):
            # UnexpectedResponse is raised when the collection doesn't exist, which is fine, since it might be a new index.
            pass
        global_summary_store.insert_nodes(new_nodes)
        global_summary_store.storage_context.persist(persist_dir=global_persist_dir)

    def get_summary(self, document_id: str) -> Optional[str]:
        with _write_lock:
            persist_dir = self.__persist_dir()
            summary_store = self.__summary_indexer(persist_dir)
            if document_id not in summary_store.index_struct.doc_id_to_summary_id:
                return None
            return summary_store.get_document_summary(document_id)

    def get_full_summary(self) -> Optional[str]:
        with _write_lock:
            global_persist_dir = self.__persist_root_dir()
            global_summary_store = self.__summary_indexer(global_persist_dir)
            document_id = str(self.data_source_id)
            if (
                document_id
                not in global_summary_store.index_struct.doc_id_to_summary_id
            ):
                return None
            return global_summary_store.get_document_summary(document_id)

    def as_query_engine(self) -> BaseQueryEngine:
        persist_dir = self.__persist_dir()
        return self.__summary_indexer(persist_dir).as_query_engine(self.llm)

    def delete_document(self, document_id: str) -> None:
        with _write_lock:
            persist_dir = self.__persist_dir()
            summary_store = self.__summary_indexer(persist_dir)

            self.__update_global_summary_store(
                summary_store, deleted_node_id=document_id
            )

            summary_store.delete_ref_doc(document_id, delete_from_docstore=True)
            summary_store.storage_context.persist(persist_dir=persist_dir)
            summary_store.vector_store.delete(document_id)

    def delete_data_source(self) -> None:
        with _write_lock:
            SummaryIndexer.delete_data_source_by_id(self.data_source_id)

    @staticmethod
    def delete_data_source_by_id(data_source_id: int) -> None:
        with _write_lock:
            vector_store = QdrantVectorStore.for_summaries(data_source_id)
            vector_store.delete()
            # TODO: figure out a less explosive way to do this.
            shutil.rmtree(
                SummaryIndexer.__database_dir(data_source_id), ignore_errors=True
            )
            global_persist_dir: str = SummaryIndexer.__persist_root_dir()
            try:
                configuration: Dict[str, Any] = SummaryIndexer.__index_configuration(
                    models.LLM.get_noop(),
                    models.Embedding.get_noop(),
                    data_source_id=data_source_id,
                    embed_summaries=False,
                )
                global_summary_store = SummaryIndexer.__summary_indexer_with_config(
                    global_persist_dir, configuration
                )
            except FileNotFoundError:
                ## global summary store doesn't exist, nothing to do
                return
            try:
                global_summary_store.delete_ref_doc(
                    str(data_source_id), delete_from_docstore=True
                )
                global_summary_store.storage_context.persist(
                    persist_dir=global_persist_dir
                )
            except Exception as e:
                logger.debug(f"Error deleting data source {data_source_id}: {e}")
