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

import io
import json
import logging
from pathlib import Path
from typing import List

import pandas as pd
from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
from llama_index.core.schema import Document, TextNode

from .base_reader import BaseReader, ChunksResult

logger = logging.getLogger(__name__)


class _CsvSplitter(MetadataAwareTextSplitter):
    def split_text_metadata_aware(self, text: str, metadata_str: str) -> List[str]:
        return self.split_text(text)

    def split_text(self, text: str) -> List[str]:
        buffer = io.StringIO(text)
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(buffer)
        # Convert the dataframe into a list of dictionaries, one per row
        rows = df.to_dict(orient="records")
        # Convert each dictionary into a chunk
        return [json.dumps(row, sort_keys=True) for row in rows]


class CSVReader(BaseReader):
    def load_chunks(self, file_path: Path) -> ChunksResult:
        ret = ChunksResult()

        # Create the base document
        with open(file_path, "r") as f:
            content = f.read()

        secrets = self._block_secrets([content])
        if secrets is not None:
            ret.secret_types = secrets
            return ret

        anonymized_text = self._anonymize_pii(content)
        if anonymized_text is not None:
            ret.pii_found = True
            content = anonymized_text

        document = Document(text=content)
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)

        local_splitter = _CsvSplitter()
        try:
            rows = local_splitter.get_nodes_from_documents([document])
        except Exception as e:
            logger.error(f"Error splitting CSV file {file_path}: {e}")
            return ret

        for i, row in enumerate(rows):
            row.metadata["file_name"] = document.metadata["file_name"]
            row.metadata["document_id"] = document.metadata["document_id"]
            row.metadata["data_source_id"] = document.metadata["data_source_id"]
            row.metadata["chunk_number"] = i
            row.metadata["row_number"] = i + 1

        converted_rows: List[TextNode] = []
        for row in rows:
            assert isinstance(row, TextNode)
            converted_rows.append(row)

        ret.chunks = converted_rows
        return ret
