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
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

from llama_index.core.schema import TextNode
from llama_index.readers.file import PDFReader as LlamaIndexPDFReader

from .base_reader import BaseReader
from .simple_file import SimpleFileReader

logger = logging.getLogger(__name__)


class PDFReader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.inner = LlamaIndexPDFReader(return_full_document=True)
        self.markdown_reader = SimpleFileReader(*args, **kwargs)


    def load_chunks(self, file_path: Path) -> list[TextNode]:
        logger.debug(f"{file_path=}")
        chunks: list[TextNode] = self.process_with_docling(file_path)
        if chunks:
            return chunks

        logger.info("Failed to convert pdf to markdown, falling back to pdf reader")
        documents = self.inner.load_data(file_path)
        assert len(documents) == 1
        document = documents[0]
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)
        return self._chunks_in_document(document)


    def process_with_docling(self, file_path):
        docling_enabled = os.getenv("USE_ENHANCED_PDF_PROCESSING", "false").lower() == "true"
        if not docling_enabled:
            return None
        directory = file_path.parent
        logger.debug(f"{directory=}")
        with open("docling-output.txt", "a") as f:
            process: CompletedProcess[bytes] = subprocess.run(
                ["docling", "-v", "--abort-on-error", f"--output={directory}", str(file_path)], stdout=f, stderr=f)
        logger.debug(f"docling return code = {process.returncode}")
        markdown_file_path = file_path.with_suffix(".md")
        if process.returncode == 0 and markdown_file_path.exists():
            # update chunk metadata to point at the original pdf
            chunks = self.markdown_reader.load_chunks(markdown_file_path)
            for chunk in chunks:
                chunk.metadata["file_name"] = file_path.name
            return chunks
        return None
