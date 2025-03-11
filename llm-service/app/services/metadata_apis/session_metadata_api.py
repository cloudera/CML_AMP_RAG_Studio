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
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

import requests

from app.services.utils import raise_for_http_error, body_to_json


@dataclass
class SessionQueryConfiguration:
    enable_hyde: bool
    enable_summary_filter: bool


@dataclass
class Session:
    id: int
    name: str
    data_source_ids: List[int]
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    inference_model: str
    rerank_model: str
    response_chunks: int
    query_configuration: SessionQueryConfiguration


@dataclass
class UpdatableSession:
    id: int
    name: str
    dataSourceIds: List[int]
    inferenceModel: str
    rerankModel: str
    responseChunks: int
    queryConfiguration: dict[str, bool]


BACKEND_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
url_template = BACKEND_BASE_URL + "/api/v1/rag/sessions/{}"


def get_session(session_id: int) -> Session:
    response = requests.get(url_template.format(session_id))
    raise_for_http_error(response)
    data = body_to_json(response)
    return Session(
        id=data["id"],
        name=data["name"],
        data_source_ids=data["dataSourceIds"],
        time_created=datetime.fromtimestamp(data["timeCreated"]),
        time_updated=datetime.fromtimestamp(data["timeUpdated"]),
        created_by_id=data["createdById"],
        updated_by_id=data["updatedById"],
        inference_model=data["inferenceModel"],
        rerank_model=data["rerankModel"],
        response_chunks=data["responseChunks"],
        query_configuration=SessionQueryConfiguration(  # TODO: automatically parse a dict into the dataclass?
            enable_hyde=data["queryConfiguration"]["enableHyde"],
            enable_summary_filter=data["queryConfiguration"]["enableSummaryFilter"],
        ),
    )


def update_session(session: Session) -> Session:
    updatable_session = UpdatableSession(
        id=session.id,
        name=session.name,
        dataSourceIds=session.data_source_ids or [],
        inferenceModel=session.inference_model,
        rerankModel=session.rerank_model,
        responseChunks=session.response_chunks,
        queryConfiguration={
            "enableHyde": session.query_configuration.enable_hyde,
            "enableSummaryFilter": session.query_configuration.enable_summary_filter,
        },
    )
    response = requests.post(
        url_template.format(updatable_session.id),
        data=json.dumps(updatable_session.__dict__, default=str),
        headers={"Content-Type": "application/json"},
        timeout=10,  # Add a timeout of 10 seconds
    )
    print(f"{response.text=}")
    return json.loads(response.text)
