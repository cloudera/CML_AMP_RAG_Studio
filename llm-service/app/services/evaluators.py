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

from llama_index.core.base.response.schema import Response
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.llms.bedrock import Bedrock

from .llama_utils import completion_to_prompt, messages_to_prompt


def evaluate_response(
    query: str,
    chat_response: AgentChatResponse,
) -> tuple[float, float]:
    evaluator_llm = Bedrock(
        model="meta.llama3-8b-instruct-v1:0",
        context_size=128000,
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
    )

    relevancy_evaluator = RelevancyEvaluator(llm=evaluator_llm)
    relevance = relevancy_evaluator.evaluate_response(
        query=query, response=Response(response=chat_response.response)
    )
    faithfulness_evaluator = FaithfulnessEvaluator(llm=evaluator_llm)
    faithfulness = faithfulness_evaluator.evaluate_response(
        query=query, response=Response(response=chat_response.response)
    )
    return relevance.score or 0, faithfulness.score or 0
