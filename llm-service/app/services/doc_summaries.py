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
import os
from typing import cast

from llama_index.core import (
    DocumentSummaryIndex,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter

from ..ai.vector_stores.qdrant import QdrantVectorStore
from ..config import settings
from . import data_sources_metadata_api, models

SUMMARY_PROMPT = 'Summarize the document into a single sentence. If an adequate summary is not possible, please return "No summary available.".'


def index_dir(data_source_id: int) -> str:
    """Return the directory name to be used for a data source's summary index."""
    return os.path.join(
        settings.rag_databases_dir, f"doc_summary_index_{data_source_id}"
    )


## todo: move to somewhere better; these are defaults to use when none are explicitly provided
def _set_settings_globals(data_source_id: int, read_only_mode: bool = True) -> None:
    metadata = data_sources_metadata_api.get_metadata(data_source_id)
    if read_only_mode:
        Settings.llm = models.get_noop_llm_model()
        Settings.embed_model = models.get_noop_embedding_model()
    else:
        Settings.llm = models.get_llm(metadata.summarization_model)
        Settings.embed_model = models.get_embedding_model(metadata.embedding_model)
    Settings.text_splitter = SentenceSplitter(chunk_size=1024)


def load_document_summary_index(
    storage_context: StorageContext, data_source_id: int, read_only_mode: bool = True
) -> DocumentSummaryIndex:
    _set_settings_globals(data_source_id, read_only_mode)
    doc_summary_index: DocumentSummaryIndex = cast(
        DocumentSummaryIndex,
        load_index_from_storage(storage_context, summary_query=SUMMARY_PROMPT),
    )
    return doc_summary_index


def summarize_data_source(data_source_id: int) -> str:
    """Return a summary of all documents in the data source."""
    metadata = data_sources_metadata_api.get_metadata(data_source_id)
    if not metadata.summarization_model:
        return "Summarization disabled.  Please specify a summarization model in the knowledge base to enable."

    index = index_dir(data_source_id)
    if not os.path.exists(index):
        return ""

    storage_context = make_storage_context(data_source_id)
    doc_summary_index = load_document_summary_index(storage_context, data_source_id)
    doc_ids = doc_summary_index.index_struct.doc_id_to_summary_id.keys()
    summaries = map(doc_summary_index.get_document_summary, doc_ids)

    prompt = 'I have summarized a list of documents that may or may not be related to each other. Please provide an overview of the document corpus as an executive summary.  Do not start with "Here is...".  The summary should be concise and not be frivolous'
    response = models.get_llm(metadata.summarization_model).complete(
        prompt + "\n".join(summaries)
    )
    return response.text


def make_storage_context(data_source_id: int) -> StorageContext:
    storage_context = StorageContext.from_defaults(
        persist_dir=index_dir(data_source_id),
        vector_store=QdrantVectorStore.for_summaries(
            data_source_id
        ).llama_vector_store(),
    )
    return storage_context
