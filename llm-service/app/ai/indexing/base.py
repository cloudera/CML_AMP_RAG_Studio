import time
start_time = time.time()
import os
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Type, Optional

from .readers.base_reader import BaseReader, ReaderConfig
from .readers.csv import CSVReader
from .readers.docx import DocxReader
from .readers.images import ImagesReader
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
    ".jpg": ImagesReader,
    ".jpeg": ImagesReader,
    ".png": ImagesReader,
}


@dataclass
class NotSupportedFileExtensionError(Exception):
    file_extension: str


class BaseTextIndexer:
    def __init__(
        self,
        data_source_id: int,
        reader_config: Optional[ReaderConfig] = None,
    ):
        self.data_source_id = data_source_id
        self.reader_config = reader_config

    @abstractmethod
    def index_file(self, file_path: Path, doc_id: str) -> None:
        pass

    def _get_reader_class(self, file_path: Path) -> Type[BaseReader]:
        file_extension = os.path.splitext(file_path)[1]
        reader_cls = READERS.get(file_extension)
        if not reader_cls:
            raise NotSupportedFileExtensionError(file_extension)

        return reader_cls


def get_reader_class(file_path: Path) -> Type[BaseReader]:
    file_extension = os.path.splitext(file_path)[1]
    reader_cls = READERS.get(file_extension)
    if not reader_cls:
        raise NotSupportedFileExtensionError(file_extension)

    return reader_cls

print(f'ai/indexing/base.py took {time.time() - start_time:.3f} seconds to import')
