#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
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
from pathlib import Path
from typing import List, Any

from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker, BaseChunk
from docling_core.transforms.serializer.base import SerializationResult
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from llama_index.core.schema import Document, TextNode, NodeRelationship

from .base_reader import BaseReader
from .base_reader import ChunksResult
from .pdf import MarkdownSerializerProvider

logger = logging.getLogger(__name__)

class DoclingReader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def load_chunks(self, file_path: Path) -> ChunksResult:
        document = Document()
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)
        parent = document.as_related_node_info()

        converted_chunks: List[TextNode] = []
        logger.debug(f"{file_path=}")
        docling_doc: ConversionResult = DocumentConverter().convert(file_path)
        chunky_chunks = HierarchicalChunker(serializer_provider=MarkdownSerializerProvider()).chunk(docling_doc.document)
        chunky_chunk: BaseChunk
        serializer = MarkdownDocSerializer(doc=docling_doc.document)
        for i, chunky_chunk in enumerate(chunky_chunks):
            text = ""
            page_number: int = 0
            for item in chunky_chunk.meta.doc_items:
                page_number= item.prov[0].page_no if item.prov else None
                item_ser: SerializationResult = serializer.serialize(item=item)
                text += item_ser.text
            node = TextNode(text=text)
            if page_number:
                node.metadata["page_number"] = page_number
            node.metadata["file_name"] = document.metadata["file_name"]
            node.metadata["document_id"] = document.metadata["document_id"]
            node.metadata["data_source_id"] = document.metadata["data_source_id"]
            node.metadata["chunk_number"] = i
            node.metadata["chunk_format"] = "markdown"
            node.relationships.update(
                {NodeRelationship.SOURCE: parent}
            )
            converted_chunks.append(node)

        return ChunksResult(converted_chunks)
