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
from typing import Any, Callable, Dict, List, Sequence

import requests
from fastapi import HTTPException
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM

from .CaiiEmbeddingModel import CaiiEmbeddingModel
from .CaiiModel import CaiiModel, CaiiModelMistral


def describe_endpoint(domain: str, endpoint_name: str) -> Any:
    with open("/tmp/jwt", "r") as file:
        jwt_contents = json.load(file)
    access_token = jwt_contents["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    describe_url = f"https://{domain}/api/v1alpha1/describeEndpoint"
    desc_json = {"name": endpoint_name, "namespace": "serving-default"}

    desc = requests.post(describe_url, headers=headers, json=desc_json)
    if desc.status_code == 404:
        raise HTTPException(
            status_code=404, detail=f"Endpoint '{endpoint_name}' not found"
        )
    return json.loads(desc.content)


def get_llm(
    domain: str,
    endpoint_name: str,
    messages_to_prompt: Callable[[Sequence[ChatMessage]], str],
    completion_to_prompt: Callable[[str], str],
) -> LLM:
    endpoint = describe_endpoint(domain=domain, endpoint_name=endpoint_name)
    api_base = endpoint["url"].removesuffix("/chat/completions")
    with open("/tmp/jwt", "r") as file:
        jwt_contents = json.load(file)
    access_token = jwt_contents["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    model = endpoint["endpointmetadata"]["model_name"]
    if "mistral" in endpoint_name.lower():
        llm = CaiiModelMistral(
            model=model,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            api_base=api_base,
            context=128000,
            default_headers=headers,
        )

    else:
        llm = CaiiModel(
            model=model,
            context=128000,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            api_base=api_base,
            default_headers=headers,
        )

    return llm


def get_embedding_model() -> BaseEmbedding:
    domain = os.environ["CAII_DOMAIN"]
    endpoint_name = os.environ["CAII_EMBEDDING_ENDPOINT_NAME"]
    endpoint = describe_endpoint(domain=domain, endpoint_name=endpoint_name)
    return CaiiEmbeddingModel(endpoint=endpoint)


### metadata methods below here


def get_caii_llm_models() -> List[Dict[str, Any]]:
    domain = os.environ["CAII_DOMAIN"]
    endpoint_name = os.environ["CAII_INFERENCE_ENDPOINT_NAME"]
    try:
        models = describe_endpoint(domain=domain, endpoint_name=endpoint_name)
    except requests.exceptions.ConnectionError as e:
        print(e)
        raise HTTPException(
            status_code=421,
            detail=f"Unable to connect to host {domain}. Please check your CAII_DOMAIN env variable.",
        )
    except HTTPException as e:
        if e.status_code == 404:
            return [{"model_id": endpoint_name}]
        else:
            raise e
    return build_model_response(models)


def get_caii_embedding_models() -> List[Dict[str, Any]]:
    # notes:
    # NameResolutionError is we can't contact the CAII_DOMAIN

    domain = os.environ["CAII_DOMAIN"]
    endpoint_name = os.environ["CAII_EMBEDDING_ENDPOINT_NAME"]
    try:
        models = describe_endpoint(domain=domain, endpoint_name=endpoint_name)
    except requests.exceptions.ConnectionError as e:
        print(e)
        raise HTTPException(
            status_code=421,
            detail=f"Unable to connect to host {domain}. Please check your CAII_DOMAIN env variable.",
        )
    except HTTPException as e:
        if e.status_code == 404:
            return [{"model_id": endpoint_name}]
        else:
            raise e
    return build_model_response(models)


def build_model_response(models: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "model_id": models["name"],
            "name": models["name"],
            "available": models["replica_count"] > 0,
            "replica_count": models["replica_count"],
        }
    ]
