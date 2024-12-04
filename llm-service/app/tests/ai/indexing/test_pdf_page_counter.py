import tempfile
import uuid
from pathlib import Path

from app.ai.indexing.pdf import PageCounter


def test_pdf_page_counter() -> None:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    # Create a simple pdf file with 3 pages
    with open(temp_file.name, "w") as f:
        f.write("page 1\npage 2\npage 3")

    page_counter = PageCounter(Path(temp_file.name))
    chunks = page_counter.load_chunks(Path(temp_file.name))
    assert len(chunks) == 3
    assert chunks[0].metadata["page_number"] == "1"
    assert chunks[1].metadata["page_number"] == "2"
    assert chunks[2].metadata["page_number"] == "3"