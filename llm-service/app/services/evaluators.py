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
import asyncio

from llama_index.core.base.response.schema import Response
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.evaluation import (
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    EvaluationResult,
)
from llama_index.core.llms import LLM

from ..services import models


def evaluate_response(query: str, chat_response: AgentChatResponse, model_name: str) -> tuple[float, float]:
    """
    Synchronous wrapper for running async evaluation of a chat response.
    """
    # Note: In a fully async application, you would await the async function directly.
    # This function fetches the model and runs the async evaluation loop.
    evaluator_llm = models.LLM.get(model_name)
    return asyncio.run(_async_evaluate_response(query, chat_response, evaluator_llm))


async def _async_evaluate_response(query: str, chat_response: AgentChatResponse, evaluator_llm: LLM) -> tuple[float, float]:
    """
    Asynchronously evaluates a chat response for relevancy and faithfulness concurrently.
    """
    response_obj = _build_response_object(chat_response)

    # Run evaluations concurrently for better performance
    relevancy_task = _evaluate_relevancy(response_obj, evaluator_llm, query)
    faithfulness_task = _evaluate_faithfulness(response_obj, evaluator_llm, query)

    relevancy_result, faithfulness_result = await asyncio.gather(relevancy_task, faithfulness_task)

    return relevancy_result.score or 0.0, faithfulness_result.score or 0.0


async def _evaluate_faithfulness(response: Response, evaluator_llm: LLM, query: str) -> EvaluationResult:
    faithfulness_evaluator = FaithfulnessEvaluator(llm=evaluator_llm)
    return await faithfulness_evaluator.aevaluate_response(query=query, response=response)


async def _evaluate_relevancy(response: Response, evaluator_llm: LLM, query: str) -> EvaluationResult:
    relevancy_evaluator = RelevancyEvaluator(llm=evaluator_llm)
    return await relevancy_evaluator.aevaluate_response(query=query, response=response)


def _build_response_object(chat_response: AgentChatResponse) -> Response:
    """Helper to construct a LlamaIndex Response object from an AgentChatResponse."""
    return Response(
        response=chat_response.response,
        source_nodes=chat_response.source_nodes,
        metadata=chat_response.metadata,
    )
