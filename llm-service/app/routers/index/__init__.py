# ##############################################################################
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

from ... import exceptions
from ...services import qdrant, s3
from ...services.chat import (generate_suggested_questions, v2_chat)
from ...services.chat_store import RagContext, RagStudioChatMessage
from . import data_source
from . import sessions
from . import amp_update
from . import models

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/index",
    tags=["index"],
)
router.include_router(data_source.router)
router.include_router(sessions.router)
router.include_router(amp_update.router)
router.include_router(models.router)


class RagIndexDocumentRequest(BaseModel):
    data_source_id: int
    s3_bucket_name: str
    s3_document_key: str
    configuration: qdrant.RagIndexDocumentConfiguration = (
        qdrant.RagIndexDocumentConfiguration()
    )


@router.post(
    "/download-and-index",
    summary="Download and index document",
    description="Download document from S3 and index in Pinecone",
)
@exceptions.propagates
def download_and_index(
    request: RagIndexDocumentRequest,
) -> str:
    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug("created temporary directory %s", tmpdirname)
        s3.download(tmpdirname, request.s3_bucket_name, request.s3_document_key)
        qdrant.download_and_index(
            tmpdirname,
            request.data_source_id,
            request.configuration,
            request.s3_document_key
        )
        return http.HTTPStatus.OK.phrase


class SuggestQuestionsRequest(BaseModel):
    data_source_id: int
    chat_history: list[RagContext]
    configuration: qdrant.RagPredictConfiguration = qdrant.RagPredictConfiguration()

class RagSuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[str]


@router.post("/suggest-questions", summary="Suggest questions with context")
@exceptions.propagates
def suggest_questions(
    request: SuggestQuestionsRequest,
) -> RagSuggestedQuestionsResponse:
    data_source_size = qdrant.size_of(request.data_source_id)
    qdrant.check_data_source_exists(data_source_size)
    suggested_questions = generate_suggested_questions(
        request.configuration, request.data_source_id, request.chat_history, data_source_size
    )
    return RagSuggestedQuestionsResponse(suggested_questions=suggested_questions)

class RagStudioChatRequest(BaseModel):
    data_source_id: int
    session_id: int
    query: str
    configuration: qdrant.RagPredictConfiguration


@router.post("/chat", summary="Chat with your documents in the requested datasource")
@exceptions.propagates
def chat(
    request: RagStudioChatRequest,
) -> RagStudioChatMessage:
    return v2_chat(request.session_id, request.data_source_id, request.query, request.configuration)
