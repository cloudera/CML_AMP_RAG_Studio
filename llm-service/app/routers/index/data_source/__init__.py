# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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
# ##############################################################################

import http
import logging
import tempfile

from fastapi import APIRouter
from pydantic import BaseModel

from .... import exceptions
from ....services import doc_summaries, qdrant, s3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data_sources/{data_source_id}", tags=["Data Sources"])


class SummarizeDocumentRequest(BaseModel):
    s3_bucket_name: str
    s3_document_key: str


@router.get("/size", summary="Returns the number of chunks in the data source.")
@exceptions.propagates
def size(data_source_id: int) -> int:
    data_source_size = qdrant.size_of(data_source_id)
    qdrant.check_data_source_exists(data_source_size)
    return data_source_size


@router.get("/chunks/{chunk_id}", summary="Returns the content of a chunk.")
@exceptions.propagates
def chunk_contents(data_source_id: int, chunk_id: str) -> str:
    return qdrant.chunk_contents(data_source_id, chunk_id)


@router.delete("", summary="Deletes the data source from the index.")
@exceptions.propagates
def delete(data_source_id: int) -> None:
    qdrant.delete(data_source_id)
    doc_summaries.delete_data_source(data_source_id)


@router.get("/documents/{doc_id}/summary", summary="summarize a single document")
@exceptions.propagates
def get_document_summary(data_source_id: int, doc_id: str) -> str:
    summaries = doc_summaries.read_summary(data_source_id, doc_id)
    return summaries


@router.get("/summary", summary="summarize all documents for a datasource")
@exceptions.propagates
def get_document_summary_of_summaries(data_source_id: int) -> str:
    return doc_summaries.summarize_data_source(data_source_id)


@router.post("/summarize-document", summary="summarize a document")
@exceptions.propagates
def summarize_document(
    data_source_id: int,
    request: SummarizeDocumentRequest,
) -> str:
    return doc_summaries.generate_summary(
        data_source_id, request.s3_bucket_name, request.s3_document_key
    )


@router.delete("/documents/{doc_id}", summary="delete a single document")
@exceptions.propagates
def delete_document(data_source_id: int, doc_id: str) -> None:
    qdrant.delete_document(data_source_id, doc_id)
    doc_summaries.delete_document(data_source_id, doc_id)



class RagIndexDocumentRequest(BaseModel):
    s3_bucket_name: str
    s3_document_key: str
    configuration: qdrant.RagIndexDocumentConfiguration = (
        qdrant.RagIndexDocumentConfiguration()
    )


@router.post(
    "/documents/download-and-index",
    summary="Download and index document",
    description="Download document from S3 and index in Pinecone",
)
@exceptions.propagates
def download_and_index(
        data_source_id: int,
        request: RagIndexDocumentRequest,
) -> str:
    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug("created temporary directory %s", tmpdirname)
        filename = s3.download(tmpdirname, request.s3_bucket_name, request.s3_document_key)
        qdrant.index(
            tmpdirname,
            data_source_id,
            request.configuration,
            request.s3_document_key,
            filename
        )
        return http.HTTPStatus.OK.phrase

