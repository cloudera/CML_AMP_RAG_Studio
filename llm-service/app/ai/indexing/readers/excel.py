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

import json
import logging
from pathlib import Path
from typing import List, cast

import pandas as pd
from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
from llama_index.core.schema import Document, TextNode

from .base_reader import BaseReader, ChunksResult


logger = logging.getLogger(__name__)


class _ExcelSplitter(MetadataAwareTextSplitter):
    """Custom splitter for XLSX files that handles multiple sheets and converts rows to JSON."""

    def split_text_metadata_aware(self, text: str, metadata_str: str) -> List[str]:
        return self.split_text(text)

    def split_text(self, text: str) -> List[str]:
        """
        Expects text to be a JSON representation of the workbook:
        {"sheets": [{"name": "Sheet1", "rows": [...]}, ...]}
        Returns one JSON string per row with embedded sheet metadata.
        """
        try:
            workbook_data = json.loads(text)
            row_chunks: List[str] = []

            for sheet_data in workbook_data.get("sheets", []):
                sheet_name = sheet_data.get("name", "")
                rows = sheet_data.get("rows", [])

                for i, row in enumerate(rows):
                    # Embed sheet metadata in the row JSON
                    row_with_meta = {
                        "__sheet_name__": sheet_name,
                        "__row_number__": i + 1,
                        **row,
                    }
                    row_chunks.append(json.dumps(row_with_meta, sort_keys=True))

            return row_chunks
        except Exception as e:
            logger.error("Error splitting XLSX text: %s", e)
            return []


class ExcelReader(BaseReader):
    def load_chunks(self, file_path: Path) -> ChunksResult:
        ret = ChunksResult()

        try:
            # Read all sheets into a dict of {sheet_name: DataFrame}
            sheets = pd.read_excel(file_path, sheet_name=None, engine="calamine")
        except Exception as e:
            logger.error("Error reading Excel file %s: %s", file_path, e)
            return ret

        # Convert workbook to JSON representation for the splitter
        workbook_data = {
            "sheets": [
                {
                    "name": str(sheet_name),
                    "rows": df.to_dict(orient="records") if df is not None else [],
                }
                for sheet_name, df in sheets.items()
            ]
        }
        content = json.dumps(workbook_data)

        # Check for secrets in the serialized content
        secrets = self._block_secrets([content])
        if secrets is not None:
            ret.secret_types = secrets
            return ret

        # Optionally anonymize PII
        anonymized_text = self._anonymize_pii(content)
        if anonymized_text is not None:
            ret.pii_found = True
            content = anonymized_text

        # Create document and use splitter
        document = Document(text=content)
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)

        local_splitter = _ExcelSplitter()

        try:
            # LlamaIndex annotates NodeParser.get_nodes_from_documents() as returning list[BaseNode]
            # but because MetadataAwareTextSplitter._parse_nodes() calls build_nodes_from_splits(),
            # it's actually list[TextNode] for our _ExcelSplitter
            rows = cast(list[TextNode], local_splitter.get_nodes_from_documents([document]))
        except Exception as e:
            logger.error("Error processing XLSX file %s: %s", file_path, e)
            return ret

        # Extract embedded metadata and clean up the row JSON
        for i, row in enumerate(rows):
            try:
                row_data = json.loads(row.text)
                sheet_name = row_data.pop("__sheet_name__", "")
                row_number = row_data.pop("__row_number__", i + 1)

                # Store cleaned row JSON without metadata fields
                row.text = json.dumps(row_data, sort_keys=True)

                # Add metadata
                row.metadata["file_name"] = document.metadata["file_name"]
                row.metadata["document_id"] = document.metadata["document_id"]
                row.metadata["data_source_id"] = document.metadata["data_source_id"]
                row.metadata["chunk_number"] = i
                row.metadata["row_number"] = row_number
                row.metadata["sheet_name"] = sheet_name
                row.metadata["chunk_format"] = "json"
            except Exception as e:
                logger.error("Error processing row %d: %s", i, e)

        ret.chunks = rows
        return ret
