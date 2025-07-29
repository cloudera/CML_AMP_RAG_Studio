#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
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

"""This script reconstructs RAG Studio's databases/doc_summary_index_global/index_store.json if somehow it (and only it) is corrupted.

NOTE:

* Make sure to back up the global directory!

Requirements:

* databases/doc_summary_index_global/docstore.json must exist.
* Run this script from the llm-service/ directory:
  ```python
  uv run python scripts/restore_global_index.py
  ```

"""
import json
import os
import sys
import uuid
from collections import defaultdict
from time import sleep
from typing import Any

from llama_index.core.schema import (
    NodeRelationship,
    ObjectType,
)
from llama_index.core.storage.docstore.types import (
    DEFAULT_PERSIST_FNAME as DEFAULT_DOC_STORE_FILENAME,
)
from llama_index.core.storage.index_store.types import (
    DEFAULT_PERSIST_FNAME as DEFAULT_INDEX_STORE_FILENAME,
)
from pydantic import BaseModel

sys.path.append(".")
from app.ai.indexing.summary_indexer import SummaryIndexer

GLOBAL_PERSIST_DIR = SummaryIndexer._SummaryIndexer__persist_root_dir()
GLOBAL_INDEX_STORE_FILEPATH = os.path.join(
    GLOBAL_PERSIST_DIR,
    DEFAULT_INDEX_STORE_FILENAME,
)
GLOBAL_DOC_STORE_FILEPATH = os.path.join(
    GLOBAL_PERSIST_DIR,
    DEFAULT_DOC_STORE_FILENAME,
)


def load_doc_store() -> dict[str, Any]:
    with open(GLOBAL_DOC_STORE_FILEPATH, "r") as f:
        return json.load(f)


def write_index_store(index_store: dict[str, Any]) -> None:
    with open(GLOBAL_INDEX_STORE_FILEPATH, "w") as f:
        json.dump(index_store, f)


class DataSource(BaseModel):
    id: int
    summary_id: uuid.UUID
    doc_summary_ids: list[uuid.UUID]


def build_index_store(data_sources: list[DataSource]) -> dict[str, Any]:
    id_ = str(uuid.uuid4())

    data = {
        "index_id": id_,
        "summary": None,
        "summary_id_to_node_ids": {
            str(data_source.summary_id): list(map(str, data_source.doc_summary_ids))
            for data_source in data_sources
        },
        "node_id_to_summary_id": {
            str(doc_summary_id): str(data_source.summary_id)
            for data_source in data_sources
            for doc_summary_id in data_source.doc_summary_ids
        },
        "doc_id_to_summary_id": {
            str(data_source.id): str(data_source.summary_id)
            for data_source in data_sources
        },
    }

    return {
        "index_store/data": {
            id_: {
                "__type__": "document_summary",
                "__data__": json.dumps(data),
            }
        }
    }


def read_doc_store(doc_store: dict[str, Any]) -> list[DataSource]:
    data_sources: dict[str, dict[str, Any]] = {}
    documents: dict[str, dict[str, Any]] = {}
    for summary_id, summary in doc_store["docstore/data"].items():
        match summary_type := summary["__type__"]:
            case ObjectType.TEXT:  # data source
                data_sources[summary_id] = summary
            case ObjectType.DOCUMENT:  # document
                documents[summary_id] = summary
            case _:
                raise ValueError(
                    f"Unrecognized type for {summary_type} summary {summary_id}"
                )

    data_source_documents: dict[int, list[str]] = defaultdict(list)
    for summary in documents.values():
        summary = summary["__data__"]
        source = summary["relationships"][NodeRelationship.SOURCE]

        data_source_documents[source["node_id"]].append(summary["id_"])

    ret: list[DataSource] = []
    for summary in data_sources.values():
        summary = summary["__data__"]
        source = summary["relationships"][NodeRelationship.SOURCE]

        data_source = DataSource(
            id=source["node_id"],
            summary_id=summary["id_"],
            doc_summary_ids=data_source_documents[source["node_id"]],
        )
        print(
            f"Collected data source {data_source.id}",
            f"with {len(data_source.doc_summary_ids)} documents.",
        )
        ret.append(data_source)
    return ret


def main() -> None:
    doc_store = load_doc_store()
    data_sources = read_doc_store(doc_store)
    index_store = build_index_store(data_sources)

    print(
        "Waiting 5 seconds before writing index",
        "in case we want to cancel or something.",
    )
    sleep(5)
    write_index_store(index_store)
    print("It is written.")


if __name__ == "__main__":
    main()
