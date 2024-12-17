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
from typing import Any, List

from llama_index.core.schema import Document, TextNode
from llama_index.readers.file import PDFReader as LlamaIndexPDFReader

from .base_reader import BaseReader
from .markdown import MdReader

logger = logging.getLogger(__name__)


class PageTracker:
    def __init__(self, pages: List[Document]) -> None:
        self.page_numbers = [page.metadata["page_label"] for page in pages]
        self.page_contents: List[str] = [page.text for page in pages]
        self.page_start_index: List[int] = [0]
        for i, text in enumerate(self.page_contents):
            # The number of characters from the start of the document to that page (add one for the newline)
            start_of_page = self.page_start_index[-1] + len(text) + 1
            self.page_start_index.append(start_of_page)
        self.document_text = "\n".join(self.page_contents)
        self.assert_correctness()

    def assert_correctness(self) -> None:
        # Check computation. Add 1 to length because we're assuming the last page would have the new line
        document_length = len(self.document_text)
        if self.page_start_index[-1] != document_length + 1:
            raise Exception(
                f"Start of page after last {self.page_start_index[-1]} does not match document text length {document_length + 1}"
            )

    def _find_page_number(self, start_index: int) -> str:
        last_good_page_number = ""
        for j, page_start in enumerate(self.page_start_index):
            if start_index >= page_start:
                last_good_page_number = self.page_numbers[j]
            else:
                break
        return last_good_page_number

    def populate_chunk_page_numbers(self, chunks: List[TextNode]) -> None:
        for chunk in chunks:
            chunk_start = chunk.start_char_idx
            if chunk_start is not None:
                chunk_label = self._find_page_number(chunk_start)
                chunk.metadata["page_number"] = chunk_label


class PDFReader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.inner = LlamaIndexPDFReader(return_full_document=False)
        self.markdown_reader = MdReader(*args, **kwargs)

    def load_chunks(self, file_path: Path) -> list[TextNode]:
        logger.debug(f"{file_path=}")
        chunks: list[TextNode] = self.process_with_docling(file_path)
        if chunks:
            return chunks

        pages: list[Document] = self.inner.load_data(file_path)
        page_counter = PageTracker(pages)
        document = Document(text=page_counter.document_text)
        document.id_ = self.document_id
        self._add_document_metadata(document, file_path)
        chunks = self._chunks_in_document(document)
        page_counter.populate_chunk_page_numbers(chunks)

        return chunks

    def process_with_docling(self, file_path: Path) -> list[TextNode] | None:
        docling_enabled = (
            os.getenv("USE_ENHANCED_PDF_PROCESSING", "false").lower() == "true"
        )
        logger.info(f"{docling_enabled=}")
        if not docling_enabled:
            return None
        directory = file_path.parent
        logger.debug(f"{directory=}")
        with open("docling-output.txt", "a") as f:
            process: CompletedProcess[bytes] = subprocess.run(
                [
                    "docling",
                    "-v",
                    "--image-export-mode=placeholder",
                    "--abort-on-error",
                    f"--output={directory}",
                    str(file_path),
                ],
                stdout=f,
                stderr=f,
            )
        logger.info(f"docling return code = {process.returncode}")
        # todo: figure out page numbers & look into the docling llama-index integration
        markdown_file_path = file_path.with_suffix(".md")
        if process.returncode == 0 and markdown_file_path.exists():
            # update chunk metadata to point at the original pdf
            chunks = self.markdown_reader.load_chunks(markdown_file_path)
            for chunk in chunks:
                chunk.metadata["file_name"] = file_path.name
            return chunks
        return None
