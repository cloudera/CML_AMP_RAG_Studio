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
from typing import List, Literal

from fastapi import APIRouter

from .... import exceptions
from ....services import models
from ....services.caii.caii import describe_endpoint, build_model_response
from ....services.caii.types import ModelResponse, Endpoint

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/llm", summary="Get LLM Inference models.")
@exceptions.propagates
def get_llm_models() -> List[ModelResponse]:
    return models.LLM.list_available()


@router.get("/embeddings", summary="Get LLM Embedding models.")
@exceptions.propagates
def get_llm_embedding_models() -> List[ModelResponse]:
    return models.Embedding.list_available()


@router.get("/reranking", summary="Get reranking models.")
@exceptions.propagates
def get_reranking_models() -> List[ModelResponse]:
    return models.Reranking.list_available()


@router.get(
    "/model_source", summary="Model source enabled - Bedrock, CAII, OpenAI or Azure"
)
@exceptions.propagates
def get_model() -> models.ModelSource:
    return models.get_model_source()


@router.get(path="/caii/endpoint/{endpoint_name}", summary="Get CAII endpoint details.")
@exceptions.propagates
def get_endpoint_description(endpoint_name: str) -> ModelResponse:
    """
    Get the details of a specific CAII endpoint by its name.
    """
    endpoint = describe_endpoint(endpoint_name)
    model_response = build_model_response(endpoint)
    return model_response


@router.get("/llm/{model_name}/test", summary="Test LLM Inference model.")
@exceptions.propagates
def llm_model_test(model_name: str) -> Literal["ok"]:
    return models.LLM.test(model_name)


@router.get("/embedding/{model_name}/test", summary="Test Embedding model.")
@exceptions.propagates
def embedding_model_test(model_name: str) -> str:
    return models.Embedding.test(model_name)


@router.get("/reranking/{model_name}/test", summary="Test Reranking model.")
@exceptions.propagates
def reranking_model_test(model_name: str) -> str:
    return models.Reranking.test(model_name)
