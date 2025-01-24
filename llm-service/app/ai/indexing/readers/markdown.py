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

from pathlib import Path
from typing import Any

from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import TextNode, Document
from llama_index.readers.file import MarkdownReader

from .base_reader import BaseReader, ChunksResult


class MdReader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.inner = MarkdownReader()

    def load_chunks(self, file_path: Path) -> ChunksResult:
        with open(file_path, "r") as f:
            content = f.read()

        secrets = self._block_secrets([content])
        if secrets is not None:
            return ChunksResult(secret_types=secrets)

        ret = ChunksResult()

        anonymized_text = self._anonymize_pii(content)
        if anonymized_text is not None:
            ret.pii_found = True
            content = anonymized_text

        document = Document(text=content)
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)
        # the process here is to do a blind sentence split on the document, then let the markdown
        # parser break up the resulting chunks into nodes based on markdown sections.
        # There is a chance that doing it the opposite way might lead to better results, but
        # we don't know how to know.
        chunks_in_document: list[TextNode] = self._chunks_in_document(document)
        parser = MarkdownNodeParser()
        results : list[TextNode] = []
        for chunk in chunks_in_document:
            parsed_nodes: list[TextNode] = parser.get_nodes_from_node(chunk)
            for node in parsed_nodes:
                self._add_document_metadata(node, file_path)
                node.metadata["chunk_format"] = "markdown"
                results.append(node)
        ret.chunks = results
        return ret
