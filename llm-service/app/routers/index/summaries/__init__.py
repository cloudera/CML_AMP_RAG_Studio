import logging
from typing import cast

from fastapi import APIRouter
from llama_index.core import StorageContext, DocumentSummaryIndex, load_index_from_storage
from llama_index.core.schema import NodeRelationship
from llama_index.core.vector_stores import SimpleVectorStore

from ....services import models
from ....ai.indexing.summary_indexer import SummaryIndexer
from .... import exceptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data_sources", tags=["Data Sources"])

@router.get(
    "/summaries",
    summary="Returns all summaries of all data sources, keyed by data source ID. That's all, folks 🥕.",
    response_model=None,
)
@exceptions.propagates
def summaries() -> dict[str, str]:
    return SummaryIndexer.get_all_data_source_summaries()