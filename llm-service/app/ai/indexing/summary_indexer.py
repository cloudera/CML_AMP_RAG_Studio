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
from typing import Any, Dict, Optional, cast

from llama_index.core import (
    DocumentSummaryIndex,
    StorageContext,
    get_response_synthesizer,
    load_index_from_storage,
)
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import ResponseMode

from app.services.models import get_noop_embedding_model

from ...config import settings
from .base import get_reader_class

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = 'Summarize the document into a single sentence. If an adequate summary is not possible, please return "No summary available.".'

# Since we don't use anything fancy to store the summaries, it's possible that two threads
# try to do a write operation at the same time and we end up with a race condition.
# Basically filesystems aren't ACID, so don't pretend that they are.
# We could have a lock per data source, but this is simpler.
_write_lock = Lock()


class SummaryIndexer:
    def __init__(
        self,
        data_source_id: int,
        splitter: SentenceSplitter,
        llm: LLM,
    ):
        self.data_source_id = data_source_id
        self.splitter = splitter
        self.llm = llm

    def __persist_dir(self) -> str:
        return os.path.join(
            settings.rag_databases_dir, f"doc_summary_index_{self.data_source_id}"
        )

    def __index_kwargs(self) -> Dict[str, Any]:
        return {
            "llm": self.llm,
            "response_synthesizer": get_response_synthesizer(
                response_mode=ResponseMode.TREE_SUMMARIZE,
                llm=self.llm,
                use_async=True,
                verbose=True,
            ),
            "show_progress": True,
            "embed_model": get_noop_embedding_model(),
            "embed_summaries": False,
            "summary_query": SUMMARY_PROMPT,
        }

    def __init_summary_store(self) -> DocumentSummaryIndex:
        doc_summary_index = DocumentSummaryIndex.from_documents(
            [],
            **self.__index_kwargs(),
        )
        doc_summary_index.storage_context.persist(persist_dir=self.__persist_dir())
        return doc_summary_index

    def __summary_indexer(self) -> DocumentSummaryIndex:
        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=self.__persist_dir(),
            )
            doc_summary_index: DocumentSummaryIndex = cast(
                DocumentSummaryIndex,
                load_index_from_storage(
                    storage_context=storage_context,
                    **self.__index_kwargs(),
                ),
            )
            return doc_summary_index
        except FileNotFoundError:
            doc_summary_index = self.__init_summary_store()
            return doc_summary_index

    def index_file(self, file_path: Path, document_id: str) -> None:
        logger.debug(f"Creating summary for file {file_path}")

        reader_cls = get_reader_class(file_path)

        reader = reader_cls(
            splitter=self.splitter,
            document_id=document_id,
            data_source_id=self.data_source_id,
        )

        logger.debug(f"Parsing file: {file_path}")

        chunks = reader.load_chunks(file_path)

        with _write_lock:
            summary_store = self.__summary_indexer()
            summary_store.insert_nodes(chunks)
            summary_store.storage_context.persist(persist_dir=self.__persist_dir())

        logger.debug(f"Summary for file {file_path} created")

    def get_summary(self, document_id: str) -> Optional[str]:
        with _write_lock:
            summary_store = self.__summary_indexer()
            if document_id not in summary_store.index_struct.doc_id_to_summary_id:
                return None
            return summary_store.get_document_summary(document_id)

    def delete_document(self, document_id: str) -> None:
        with _write_lock:
            summary_store = self.__summary_indexer()
            summary_store.delete_ref_doc(document_id)
            summary_store.storage_context.persist(persist_dir=self.__persist_dir())

    def delete_data_source(self) -> None:
        with _write_lock:
            # We need to re-load the summary index constantly because of this delete.
            # TODO: figure out a less explosive way to do this.
            shutil.rmtree(self.__persist_dir())
