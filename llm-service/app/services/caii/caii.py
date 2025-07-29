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
from urllib.parse import urlparse

import httpx
import requests
from fastapi import HTTPException
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.llms.nvidia import NVIDIA
from packaging.version import Version

from .CaiiEmbeddingModel import CaiiEmbeddingModel
from .CaiiModel import DeepseekModel
from .caii_reranking import CaiiRerankingModel
from .types import Endpoint, ListEndpointEntry, ModelResponse, DescribeEndpointEntry
from .utils import (
    build_auth_headers,
    get_caii_access_token,
    get_cml_version_from_sense_bootstrap,
)
from ..llama_utils import completion_to_prompt, messages_to_prompt
from ..utils import raise_for_http_error, body_to_json
from ...config import settings

DEFAULT_NAMESPACE = "serving-default"

logger = logging.getLogger(__name__)


def describe_endpoint_entry(
    endpoint_name: str, endpoints: Optional[list[ListEndpointEntry]] = None
) -> Endpoint:
    if not endpoints:
        endpoint = describe_endpoint(endpoint_name)
        return cast(Endpoint, endpoint)

    logger.info(
        "Fetching endpoint details from cached list of endpoints for endpoint: %s",
        endpoint_name,
    )
    for endpoint in endpoints:
        if endpoint.name == endpoint_name:
            return cast(Endpoint, endpoint)

    raise HTTPException(
        status_code=404, detail=f"Endpoint '{endpoint_name}' not found."
    )


def describe_endpoint(endpoint_name: str) -> DescribeEndpointEntry:
    logger.info(
        "Fetching endpoint details from CAII REST API for endpoint: %s", endpoint_name
    )
    if ":" in endpoint_name:
        # If the endpoint name contains a colon, it should be in the format "domain:endpoint_name"
        pieces = endpoint_name.split(":")
        domain = pieces[0]
        endpoint_name = pieces[1]
    else:
        domain = settings.caii_domain
    headers = build_auth_headers()
    describe_url = f"https://{domain}/api/v1alpha1/describeEndpoint"
    desc_json = {"name": endpoint_name, "namespace": DEFAULT_NAMESPACE}

    response = requests.post(describe_url, headers=headers, json=desc_json)
    raise_for_http_error(response)
    return DescribeEndpointEntry(**body_to_json(response))


def list_endpoints() -> list[ListEndpointEntry]:
    results: list[ListEndpointEntry] = []
    version: Optional[str] = get_cml_version_from_sense_bootstrap()

    # Try Python API for CML version >= 2.0.50-b68
    if version:
        if Version(version) >= Version("2.0.50-b68"):
            logger.info("Attempting Model discovery through Python API")
            python_api_results = list_endpoints_from_python_api()
            if python_api_results:
                logger.info(
                    "Found %d endpoints via Python API.", len(python_api_results)
                )
                results.extend(python_api_results)
        else:
            logger.info(
                "CML version %s is below 2.0.50-b68, skipping Python API model discovery.",
                version,
            )
    else:
        logger.warning("CML version not found. Skipping Python API model discovery.")

    # Try CAII REST API if domain is configured
    domain = settings.caii_domain
    if not domain:
        if not results:
            logger.warning(
                "No CAII domain configured and no endpoints found via Python API."
            )
            return []
        logger.info(
            "No CAII domain configured, returning discovered endpoints: %s", results
        )
        return results

    logger.info("Using CAII domain: %s", domain)
    try:
        rest_api_results = list_endpoints_from_rest_api(domain)
        if rest_api_results:
            new_rest_api_results = []
            for endpoint in rest_api_results:
                # Only add endpoints we didn't already find via Python API
                existing_names = set([f"{e.url}:{e.name}" for e in results])
                if f"{endpoint.url}:{endpoint.name}" not in existing_names:
                    new_rest_api_results.append(endpoint)
            logger.info(
                "Found %d additional endpoints via CAII REST API.",
                len(new_rest_api_results),
            )
            results.extend(new_rest_api_results)
        else:
            logger.info("No new endpoints found via CAII REST API.")
    except Exception as e:
        logger.exception("Failed to list endpoints from CAII REST API. Error: %s", e)
        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to list endpoints from both Python API and CAII REST API.",
            )
        logger.info("Returning previously discovered endpoints: %s", results)
    if not results:
        logger.warning(
            "No endpoints found from either Python API or CAII REST API. Returning empty list."
        )
        return []
    logger.info("Total endpoints discovered: %d", len(results))
    return results


def list_endpoints_from_python_api() -> list[ListEndpointEntry]:
    try:
        import cmlapi
        import cml.endpoints_v1 as cmlendpoints

        results: list[ListEndpointEntry] = []
        api_client = cmlapi.default_client()
        ml_serving_apps = api_client.list_ml_serving_apps()
        logger.info("Listing endpoints for ML Serving Apps: %s", ml_serving_apps)
        endpoint_groups = cmlendpoints.list_endpoints(ml_serving_apps)
        for endpoints in endpoint_groups:
            for endpoint in endpoints:
                logger.info("Found endpoint: %s", endpoint)
                results.append(ListEndpointEntry(**endpoint))
        return results
    except ImportError as e:
        logger.warning("Failed to import CML Python API modules. Error: %s", e)
    except Exception as e:
        logger.exception(
            "Model discovery failed through Python API, trying CAI REST API. Error: %s",
            e,
        )
    return []


def list_endpoints_from_rest_api(domain: str) -> list[ListEndpointEntry]:
    headers = build_auth_headers()
    list_url = f"https://{domain}/api/v1alpha1/listEndpoints"
    list_json = {"namespace": DEFAULT_NAMESPACE}
    response = requests.post(list_url, headers=headers, json=list_json, timeout=10)
    raise_for_http_error(response)
    api_endpoints = body_to_json(response).get("endpoints", [])
    # Add domain prefix to endpoint names for clarity
    logger.info(f"Found {len(api_endpoints)} endpoints from CAII REST API")
    results: list[ListEndpointEntry] = []
    for entry in api_endpoints:
        if "name" not in entry or "url" not in entry:
            logger.warning("Skipping endpoint entry without 'name' or 'url': %s", entry)
            continue
        # Ensure the entry has a 'task' field, defaulting to None if missing
        results.append(
            ListEndpointEntry(
                **entry,
            )
        )
    return results


def get_reranking_model(model_name: str, top_n: int) -> BaseNodePostprocessor:
    endpoint = describe_endpoint_entry(endpoint_name=model_name)
    token = get_caii_access_token()
    return CaiiRerankingModel(
        model=endpoint.model_name,
        base_url=endpoint.url,
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
    endpoint = describe_endpoint_entry(endpoint_name=endpoint_name)
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
    endpoints: list[ListEndpointEntry] = list_endpoints()
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

    domain = urlparse(endpoint.url).hostname
    print(f"{endpoint=}, domain={domain}")
    return ModelResponse(
        model_id=f"{domain}:{endpoint.name}",
        name=endpoint.name,
    )


@build_model_response.register
def _(endpoint: DescribeEndpointEntry) -> ModelResponse:
    domain = urlparse(endpoint.url).hostname
    print(f"{endpoint=}, domain={domain}")
    return ModelResponse(
        model_id=f"{domain}:{endpoint.name}",
        name=endpoint.name,
        available=endpoint.replica_count > 0,
        replica_count=endpoint.replica_count,
    )
