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
from typing import Optional

import requests

from app.services.utils import raise_for_http_error, body_to_json


@dataclass
class RagDataSource:
    id: int
    name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap_percent: int
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    connection_type: str
    summarization_model: Optional[str] = None
    document_count: Optional[int] = None
    total_doc_size: Optional[int] = None


BACKEND_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
url_template = BACKEND_BASE_URL + "/api/v1/rag/dataSources/{}"


def get_metadata(data_source_id: int) -> RagDataSource:
    response = requests.get(url_template.format(data_source_id))
    raise_for_http_error(response)
    data = body_to_json(response)
    return RagDataSource(
        id=data["id"],
        name=data["name"],
        embedding_model=data["embeddingModel"],
        summarization_model=data.get("summarizationModel"),
        chunk_size=data["chunkSize"],
        chunk_overlap_percent=data["chunkOverlapPercent"],
        time_created=datetime.fromtimestamp(data["timeCreated"]),
        time_updated=datetime.fromtimestamp(data["timeUpdated"]),
        created_by_id=data["createdById"],
        updated_by_id=data["updatedById"],
        connection_type=data["connectionType"],
        document_count=data.get("documentCount"),
        total_doc_size=data.get("totalDocSize"),
    )
