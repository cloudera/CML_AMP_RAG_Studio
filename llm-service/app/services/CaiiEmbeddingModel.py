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
import http.client as http_client
import json
import os
from typing import Any, Dict

from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from pydantic import Field


class CaiiEmbeddingModel(BaseEmbedding):
    endpoint = Field(any, description="The endpoint to use for embeddings")

    def __init__(self, endpoint: Dict[str, Any]):
        super().__init__()
        self.endpoint = endpoint

    def _get_text_embedding(self, text: str) -> Embedding:
        return self._get_embedding(text, "passage")

    async def _aget_query_embedding(self, query: str) -> Embedding:
        raise NotImplementedError("Not implemented")

    def _get_query_embedding(self, query: str) -> Embedding:
        return self._get_embedding(query, "query")

    def _get_embedding(self, query: str, input_type: str) -> Embedding:
        model = self.endpoint["endpointmetadata"]["model_name"]
        domain = os.environ["CAII_DOMAIN"]

        connection = http_client.HTTPSConnection(domain, 443)
        headers = self.build_auth_headers()
        headers["Content-Type"] = "application/json"
        body = json.dumps(
            {
                "input": query,
                "input_type": input_type,
                "truncate": "END",
                "model": model,
            }
        )
        connection.request("POST", self.endpoint["url"], body=body, headers=headers)
        res = connection.getresponse()
        data = res.read()
        json_response = data.decode("utf-8")
        structured_response = json.loads(json_response)
        embedding = structured_response["data"][0]["embedding"]
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

        return embedding

    def build_auth_headers(self) -> Dict[str, str]:
        with open("/tmp/jwt", "r") as file:
            jwt_contents = json.load(file)
        access_token = jwt_contents["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        return headers
