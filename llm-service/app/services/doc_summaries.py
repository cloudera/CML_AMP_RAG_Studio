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
import shutil
import tempfile
import os
from typing import cast

from llama_index.core import (
    DocumentSummaryIndex,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.llms.bedrock import Bedrock
from llama_index.vector_stores.qdrant import QdrantVectorStore
from .qdrant import create_qdrant_clients

from .llama_utils import completion_to_prompt, messages_to_prompt
from .s3 import download
from .utils import get_last_segment

## todo: move to somewhere better; these are defaults to use when none are explicitly provided
Settings.llm = Bedrock(
    model="meta.llama3-8b-instruct-v1:0",
    context_size=128000,
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,
)

Settings.embed_model = BedrockEmbedding(model_name="cohere.embed-english-v3")
Settings.splitter = SentenceSplitter(chunk_size=1024)


SUMMARY_PROMPT = 'Summarize the document into a single sentence. If an adequate summary is not possible, please return "No summary available.".'


def index_dir(data_source_id: int) -> str:
    """Return the directory name to be used for a data source's summary index."""
    return f"../databases/doc_summary_index_{data_source_id}"


def read_summary(data_source_id: int, document_id: str) -> str:
    """Return the summary of `document_id`."""
    storage_context = make_storage_context(data_source_id)
    doc_summary_index = load_document_summary_index(storage_context)

    if document_id not in doc_summary_index.index_struct.doc_id_to_summary_id:
        return "No summary found for this document."

    return doc_summary_index.get_document_summary(doc_id=document_id)


def load_document_summary_index(storage_context) -> DocumentSummaryIndex:
    doc_summary_index: DocumentSummaryIndex = cast(
        DocumentSummaryIndex,
        load_index_from_storage(storage_context, summary_query=SUMMARY_PROMPT),
    )
    return doc_summary_index


def generate_summary(
    data_source_id: int,
    s3_bucket_name: str,
    s3_document_key: str,
) -> str:
    """Generate, persist, and return a summary for `s3_document_key`."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # load document(s)
        download(tmpdirname, s3_bucket_name, s3_document_key)
        documents = SimpleDirectoryReader(tmpdirname).load_data()
        document_id = get_last_segment(s3_document_key)
        for document in documents:
            document.id_ = document_id

        try:
            storage_context = make_storage_context(data_source_id)
        except FileNotFoundError:
            initialize_summary_index_storage(data_source_id)
            storage_context = make_storage_context(data_source_id)

        doc_summary_index = load_document_summary_index(storage_context)

        for document in documents:
            doc_summary_index.insert(document)
        index = index_dir(data_source_id)
        doc_summary_index.storage_context.persist(
            persist_dir=index,
        )

        return doc_summary_index.get_document_summary(doc_id=document_id)


def initialize_summary_index_storage(data_source_id):
    doc_summary_index = DocumentSummaryIndex.from_documents(
        [],
        summary_query=SUMMARY_PROMPT,
    )
    doc_summary_index.storage_context.persist(persist_dir=index_dir(data_source_id))


def summarize_data_source(data_source_id: int) -> str:
    """Return a summary of all documents in the data source."""
    index = index_dir(data_source_id)
    if not os.path.exists(index):
        return ""

    storage_context = make_storage_context(data_source_id)
    doc_summary_index = load_document_summary_index(storage_context)
    doc_ids = doc_summary_index.index_struct.doc_id_to_summary_id.keys()
    summaries = map(doc_summary_index.get_document_summary, doc_ids)

    prompt = "I have summarized a list of documents that may or may not be related to each other. Please provide an overview of the document corpus as an executive summary.  Do not start with \"Here is...\".  The summary should be concise and not be frivolous"
    response = Settings.llm.complete(prompt + "\n".join(summaries))
    return response.text


def make_storage_context(data_source_id):
    storage_context = StorageContext.from_defaults(
        persist_dir=index_dir(data_source_id),
        vector_store=create_qdrant_vector_store(data_source_id),
    )
    return storage_context

def create_qdrant_vector_store(data_source_id: int) -> QdrantVectorStore:
    vector_store = QdrantVectorStore(
        table_name_from(data_source_id), *create_qdrant_clients()
    )
    return vector_store

def table_name_from(data_source_id: int):
    return f"summary_index_{data_source_id}"


def delete_data_source(data_source_id):
    """Delete the summary index for `data_source_id`."""
    index = index_dir(data_source_id)
    if os.path.exists(index):
        shutil.rmtree(index)
    [qdrant_client, _]  = create_qdrant_clients()
    qdrant_client.delete_collection(table_name_from(data_source_id))
