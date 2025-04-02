import logging

from fastapi import APIRouter

from .... import exceptions
from ....ai.indexing.summary_indexer import SummaryIndexer

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
