import time
start_time = time.time()
import pytest
from llama_index.core import Document
from llama_index.core.schema import TextNode

from app.ai.indexing.readers.pdf import PageTracker


class TestPageTracker:
    @staticmethod
    def test_initializes_correctly() -> None:
        pages = [Document(text="Page 1"), Document(text="Page 2")]
        pages[0].metadata["page_label"] = "1"
        pages[1].metadata["page_label"] = "2"
        page_counter = PageTracker(pages)
        assert page_counter.page_numbers == ["1", "2"]
        assert page_counter.page_contents == ["Page 1", "Page 2"]
        assert page_counter.page_start_index == [0, 7, 14]
        assert page_counter.document_text == "Page 1\nPage 2"

    @staticmethod
    def test_raises_exception_on_incorrectness() -> None:
        pages = [Document(text="Page 1"), Document(text="Page 2")]
        pages[0].metadata["page_label"] = "1"
        pages[1].metadata["page_label"] = "2"
        page_counter = PageTracker(pages)
        page_counter.page_start_index[-1] = 100
        with pytest.raises(Exception):
            page_counter.assert_correctness()

    @staticmethod
    def test_finds_correct_page_number() -> None:
        pages = [Document(text="Page 1"), Document(text="Page 2")]
        pages[0].metadata["page_label"] = "1"
        pages[1].metadata["page_label"] = "2"
        page_counter = PageTracker(pages)
        assert page_counter._find_page_number(0) == "1"
        assert page_counter._find_page_number(6) == "1"
        assert page_counter._find_page_number(7) == "2"
        assert page_counter._find_page_number(10) == "2"
        assert page_counter._find_page_number(13) == "2"

    @staticmethod
    def test_populates_chunk_page_numbers() -> None:
        pages = [Document(text="Page 1"), Document(text="Page 2")]
        pages[0].metadata["page_label"] = "1"
        pages[1].metadata["page_label"] = "2"
        page_counter = PageTracker(pages)
        chunks = [
            TextNode(start_char_idx=0),
            TextNode(start_char_idx=4),
            TextNode(start_char_idx=7),
            TextNode(start_char_idx=10),
        ]
        page_counter.populate_chunk_page_numbers(chunks)
        assert chunks[0].metadata["page_number"] == "1"
        assert chunks[1].metadata["page_number"] == "1"
        assert chunks[2].metadata["page_number"] == "2"
        assert chunks[3].metadata["page_number"] == "2"

    @staticmethod
    def test_populates_chunk_page_numbers_chunk_spans_2_pages() -> None:
        pages = [Document(text="Page 1"), Document(text="Page 2")]
        pages[0].metadata["page_label"] = "1"
        pages[1].metadata["page_label"] = "2"
        page_counter = PageTracker(pages)
        chunks = [TextNode(start_char_idx=0)]
        page_counter.populate_chunk_page_numbers(chunks)
        assert chunks[0].metadata["page_number"] == "1"

print(f'tests/ai/indexing/test_pdf_page_tracker.py took {time.time() - start_time} seconds to import')
