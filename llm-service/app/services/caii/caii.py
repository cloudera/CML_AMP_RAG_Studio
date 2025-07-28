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
import functools
import logging
import os
from typing import Callable, List, Sequence, Optional, cast

import httpx
import requests
from fastapi import HTTPException
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.llms.nvidia import NVIDIA

from .CaiiEmbeddingModel import CaiiEmbeddingModel
from .CaiiModel import DeepseekModel
from .caii_reranking import CaiiRerankingModel
from .types import Endpoint, ListEndpointEntry, ModelResponse, DescribeEndpointEntry
from .utils import build_auth_headers, get_caii_access_token
from ..llama_utils import completion_to_prompt, messages_to_prompt
from ..utils import raise_for_http_error, body_to_json
from ...config import settings

DEFAULT_NAMESPACE = "serving-default"

logger = logging.getLogger(__name__)


def describe_endpoint_entry(
    endpoint_name: str, endpoints: Optional[list[ListEndpointEntry]] = None
) -> Endpoint:
    endpoint = describe_endpoint(endpoint_name)
    return cast(Endpoint, endpoint)

    # logger.info(
    #     "Fetching endpoint details from cached list of endpoints for endpoint: %s",
    #     endpoint_name,
    # )
    # for endpoint in endpoints:
    #     if endpoint.name == endpoint_name:
    #         return cast(Endpoint, endpoint)
    #
    # raise HTTPException(
    #     status_code=404, detail=f"Endpoint '{endpoint_name}' not found."
    # )


def describe_endpoint(endpoint_name: str) -> DescribeEndpointEntry:
    logger.info(
        "Fetching endpoint details from CAII REST API for endpoint: %s", endpoint_name
    )
    domain = settings.caii_domain
    headers = build_auth_headers()
    describe_url = f"https://{domain}/api/v1alpha1/describeEndpoint"
    desc_json = {"name": endpoint_name, "namespace": DEFAULT_NAMESPACE}

    response = requests.post(describe_url, headers=headers, json=desc_json)
    raise_for_http_error(response)
    return DescribeEndpointEntry(**body_to_json(response))


def list_endpoints() -> list[ListEndpointEntry]:
    try:
        logger.info("Attempting Model discovery through Python API")
        import cmlapi
        import cml.endpoints_v1 as cmlendpoints

        api_client = cmlapi.default_client()
        ml_serving_apps = api_client.list_ml_serving_apps()
        logger.info("Listing endpoints for ML Serving Apps: %s", ml_serving_apps)
        endpoints = cmlendpoints.list_endpoints(ml_serving_apps)

        return [ListEndpointEntry(**endpoint) for endpoint in endpoints]
    except Exception:
        logger.exception(
            "Model discovery failed through Python API, falling back to CAI REST API"
        )
        try:
            domain = settings.caii_domain

            headers = build_auth_headers()
            describe_url = f"https://{domain}/api/v1alpha1/listEndpoints"
            desc_json = {"namespace": DEFAULT_NAMESPACE}

            response = requests.post(
                describe_url, headers=headers, json=desc_json, timeout=5
            )
            raise_for_http_error(response)
            endpoints = body_to_json(response)["endpoints"]
            return [ListEndpointEntry(**endpoint) for endpoint in endpoints]
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=421,
                detail=f"Unable to connect to host '{domain}'. Please check your CAII Settings.",
            )


def get_reranking_model(model_name: str, top_n: int) -> BaseNodePostprocessor:
    endpoint = describe_endpoint_entry(endpoint_name=model_name)
    token = get_caii_access_token()
    return CaiiRerankingModel(
        model=endpoint.model_name,
        base_url=endpoint.url.removesuffix("/ranking"),
        api_key=token,
        top_n=top_n,
    )


def get_llm(
    endpoint: Endpoint,
    messages_to_prompt: Callable[[Sequence[ChatMessage]], str],
    completion_to_prompt: Callable[[str], str],
) -> LLM:
    api_base = endpoint.url.removesuffix("/chat/completions")

    model = endpoint.model_name
    if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
        http_client = httpx.Client(verify="/etc/ssl/certs/ca-certificates.crt")
    else:
        http_client = None

    # todo: test if the NVIDIA impl works with deepseek, too
    if "deepseek" in endpoint.name.lower():
        return DeepseekModel(
            model=model,
            context=128000,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            api_base=api_base,
            default_headers=(build_auth_headers()),
            http_client=http_client,
        )
    return NVIDIA(
        api_key=get_caii_access_token(),
        base_url=api_base,
        model=model,
        http_client=http_client,
    )


def get_embedding_model(model_name: str) -> BaseEmbedding:
    endpoint_name = model_name
    print(f"{endpoint_name=}")
    endpoint = describe_endpoint_entry(endpoint_name=endpoint_name)
    print(f"{endpoint=}")
    if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
        http_client = httpx.Client(verify="/etc/ssl/certs/ca-certificates.crt")
    else:
        http_client = None

    # todo: figure out if the Nvidia library can be made to work for embeddings as well.
    return CaiiEmbeddingModel(endpoint=endpoint, http_client=http_client)


# task types from the MLServing proto definition
# TASK_UNKNOWN = 0;
# INFERENCE = 1;
# TEXT_GENERATION = 2;
# EMBED = 3;
# TEXT_TO_TEXT_GENERATION = 4;
# CLASSIFICATION = 5;
# FILL_MASK = 6;
# RANK = 7;


def get_caii_llm_models() -> List[ModelResponse]:
    potential_models = get_models_with_task("TEXT_GENERATION")
    results: list[Endpoint] = []
    for potential in potential_models:
        try:
            model = get_llm(
                endpoint=potential,
                messages_to_prompt=messages_to_prompt,
                completion_to_prompt=completion_to_prompt,
            )
            if model.metadata:
                results.append(potential)
        except Exception as e:
            logger.warning(
                f"Unable to load model metadata for model: {potential.name}. Error: {e}"
            )
            pass

    return list(map(build_model_response, results))


def get_caii_reranking_models() -> List[ModelResponse]:
    endpoints = get_models_with_task("RANK")
    return list(map(build_model_response, endpoints))


def get_caii_embedding_models() -> List[ModelResponse]:
    endpoints = get_models_with_task("EMBED")
    return list(map(build_model_response, endpoints))


def get_models_with_task(task_type: str) -> List[Endpoint]:
    endpoints = list_endpoints()
    endpoint_details = list(
        map(
            lambda endpoint: describe_endpoint_entry(endpoint.name, endpoints),
            endpoints,
        )
    )
    llm_endpoints = list(
        filter(
            lambda endpoint: endpoint.task and endpoint.task == task_type,
            endpoint_details,
        )
    )
    return llm_endpoints


@functools.singledispatch
def build_model_response(endpoint: Endpoint) -> ModelResponse:
    print(f"{endpoint=}")
    return ModelResponse(
        model_id=endpoint.name,
        name=endpoint.name,
    )


@build_model_response.register
def _(endpoint: DescribeEndpointEntry) -> ModelResponse:
    return ModelResponse(
        model_id=endpoint.name,
        name=endpoint.name,
        available=endpoint.replica_count > 0,
        replica_count=endpoint.replica_count,
    )
