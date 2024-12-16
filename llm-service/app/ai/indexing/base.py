import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Type

from .readers.base_reader import BaseReader
from .readers.csv import CSVReader
from .readers.docx import DocxReader
from .readers.json import JSONReader
from .readers.markdown import MdReader
from .readers.pdf import PDFReader
from .readers.pptx import PptxReader
from .readers.simple_file import SimpleFileReader

READERS: Dict[str, Type[BaseReader]] = {
    ".pdf": PDFReader,
    ".txt": SimpleFileReader,
    ".md": MdReader,
    ".docx": DocxReader,
    ".pptx": PptxReader,
    ".pptm": PptxReader,
    ".ppt": PptxReader,
    ".csv": CSVReader,
    ".json": JSONReader,
}


@dataclass
class NotSupportedFileExtensionError(Exception):
    file_extension: str


def get_reader_class(file_path: Path) -> Type[BaseReader]:
    file_extension = os.path.splitext(file_path)[1]
    reader_cls = READERS.get(file_extension)
    if not reader_cls:
        raise NotSupportedFileExtensionError(file_extension)

    return reader_cls
