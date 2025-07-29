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
from typing import Generator, Optional

from llama_index.core.node_parser import SentenceSplitter

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.config import Settings
from app.services import models
from app.services.metadata_apis import data_sources_metadata_api


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
    for data_source_id in _get_data_source_ids():
        print(f"Restoring data source {data_source_id}")
        if summary_indexer := _summary_indexer(data_source_id) is None:
            continue
        summary_indexer.restore_index_store()


if __name__ == "__main__":
    main()
