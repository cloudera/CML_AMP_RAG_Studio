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
from typing import Optional
from typing import cast

from llama_index.core import (
    DocumentSummaryIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import (
    Document,
    NodeRelationship,
)
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.storage.index_store.types import DEFAULT_PERSIST_FNAME
from qdrant_client.http.exceptions import UnexpectedResponse

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.ai.vector_stores.qdrant import QdrantVectorStore
from app.config import Settings
from app.services import models
from app.services.metadata_apis import data_sources_metadata_api


def restore_index_store(self: SummaryIndexer) -> None:
    """Reconstruct the index store from scratch.

    Based on logic from
    * index_file()
    * __update_global_summary_store().
    * __init_summary_store()

    """
    global_persist_dir = self._SummaryIndexer__persist_root_dir()
    global_summary_store_config = self._SummaryIndexer__index_kwargs(
        embed_summaries=False
    )

    data_source_id: int = global_summary_store_config.get("data_source_id")

    # initialize index store
    DocumentSummaryIndex.from_documents(
        [],
        **global_summary_store_config,
    ).storage_context.index_store.persist(
        str(os.path.join(global_persist_dir, DEFAULT_PERSIST_FNAME))
    )

    # load global stores
    storage_context = StorageContext.from_defaults(
        persist_dir=global_persist_dir,
        vector_store=QdrantVectorStore.for_summaries(
            data_source_id
        ).llama_vector_store(),
    )
    global_summary_store: DocumentSummaryIndex = cast(
        DocumentSummaryIndex,
        load_index_from_storage(
            storage_context=storage_context,
            **global_summary_store_config,
        ),
    )

    # gather documents
    new_nodes: list[Document] = []
    summary_store: DocumentSummaryIndex = self._SummaryIndexer__summary_indexer(
        self._SummaryIndexer__database_dir(data_source_id)
    )
    data_source_node = Document(doc_id=str(data_source_id))
    print(f"{global_summary_store.docstore.docs=}")
    for doc_id, doc in global_summary_store.docstore.docs.items():
        # TODO: Get this working; where am I supposed to pull summaries from??
        # TODO: Do I even need the summaries? This is basically recreating the entire global summary store, but
        #       technically we only need the index.
        print(f"{global_summary_store.get_document_summary(doc_id)=}")
        new_nodes.append(
            Document(
                doc_id=doc_id,
                text=summary_store.get_document_summary(doc_id),
                relationships={
                    NodeRelationship.SOURCE: data_source_node.as_related_node_info()
                },
            )
        )

    # persist
    try:
        # Delete first so that we don't accumulate trash in the summary store.
        global_summary_store.delete_ref_doc(
            str(data_source_id), delete_from_docstore=True
        )
    except (KeyError, UnexpectedResponse):
        # UnexpectedResponse is raised when the collection doesn't exist, which is fine, since it might be a new index.
        pass
    global_summary_store.insert_nodes(new_nodes)
    global_summary_store.storage_context.persist(persist_dir=global_persist_dir)


def _get_data_source_ids() -> list[int]:
    PREFIX = "doc_summary_index_"
    DB_DIR = Settings().rag_databases_dir
    dirs = filter(
        lambda dirname: os.path.isdir(os.path.join(DB_DIR, dirname)),
        os.listdir(DB_DIR),
    )
    indexes = filter(lambda s: s.startswith(PREFIX), dirs)
    doc_summary_indexes = filter(lambda s: not s.endswith("_global"), indexes)
    data_source_ids = map(lambda s: s.removeprefix(PREFIX), doc_summary_indexes)
    return list(map(int, data_source_ids))


def _summary_indexer(data_source_id: int) -> Optional[SummaryIndexer]:
    ### START DataSourceController._get_summary_indexer() copy ###
    datasource = data_sources_metadata_api.get_metadata(data_source_id)
    if not datasource.summarization_model:
        return None
    return SummaryIndexer(
        data_source_id=data_source_id,
        splitter=SentenceSplitter(chunk_size=2048),
        embedding_model=models.Embedding.get(datasource.embedding_model),
        llm=models.LLM.get(datasource.summarization_model),
    )
    ### END DataSourceController._get_summary_indexer() copy ###


def main() -> None:
    SummaryIndexer.restore_index_store = restore_index_store

    for data_source_id in _get_data_source_ids():
        summary_indexer = _summary_indexer(data_source_id)
        if summary_indexer is None:
            print(f"Skipping data source {data_source_id}")
            continue
        print(f"Restoring data source {data_source_id}")
        summary_indexer.restore_index_store()


if __name__ == "__main__":
    main()
