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
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import requests


@dataclass
class Session:
    id: int
    name: str
    data_source_ids: List[int]
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    last_interaction_time: datetime
    inference_model: str
    response_chunks: int

BACKEND_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
url_template = BACKEND_BASE_URL + "/api/v1/rag/sessions/{}"

def get_session(session_id: int) -> Session:
    response = requests.get(url_template.format(session_id))
    response.raise_for_status()
    data = response.json()
    return Session(
        id=data["id"],
        name=data["name"],
        data_source_ids=data["dataSourceIds"],
        time_created=datetime.fromtimestamp(data["timeCreated"]),
        time_updated=datetime.fromtimestamp(data["timeUpdated"]),
        created_by_id=data["createdById"],
        updated_by_id=data["updatedById"],
        last_interaction_time=datetime.fromtimestamp(data["lastInteractionTime"]),
        inference_model=data["inferenceModel"],
        response_chunks=data["responseChunks"],
    )
