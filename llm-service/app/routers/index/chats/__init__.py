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
from typing import Optional, Annotated

from fastapi import APIRouter, Cookie

from app import exceptions
from app.rag_types import RagPredictConfiguration
from app.routers.index.sessions import RagStudioChatRequest, parse_jwt_cookie
from app.services.chat import direct_llm_chat, v2_chat
from app.services.chat_store import RagStudioChatMessage
from app.services.metadata_apis import session_metadata_api
from app.services.metadata_apis.session_metadata_api import (
    NewSession,
    SessionQueryConfiguration,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("", summary="Chat")
@exceptions.propagates
def chat(
    request: RagStudioChatRequest,
    _basusertoken: Annotated[str | None, Cookie()] = None,
) -> RagStudioChatMessage:
    user_name = parse_jwt_cookie(_basusertoken)

    temp_session = NewSession(
        name="New Chat",
        data_source_ids=[],
        inference_model=None,
        response_chunks=10,
        query_configuration=SessionQueryConfiguration(
            enable_hyde=False, enable_summary_filter=True
        ),
    )
    session = session_metadata_api.create_session(
        temp_session, user_token=_basusertoken
    )

    configuration = request.configuration or RagPredictConfiguration()
    if configuration.exclude_knowledge_base or len(session.data_source_ids) == 0:
        return direct_llm_chat(session, request.query, user_name)
    return v2_chat(session, request.query, configuration, user_name)
