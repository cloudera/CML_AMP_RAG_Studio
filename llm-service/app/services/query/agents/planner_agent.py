#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
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

import logging
from typing import Dict, Any, Optional

from crewai import Agent, Task, Crew, Process
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from pydantic import BaseModel, Field

from app.services.query.agents.models import get_crewai_llm_object_direct
from app.services.query.query_configuration import QueryConfiguration
from app.services.models.providers import BedrockModelProvider, AzureModelProvider

logger = logging.getLogger(__name__)


def get_crewai_model_name(llm: LLM) -> str:
    if AzureModelProvider.is_enabled():
        crewai_llm_name = f"azure/{llm.metadata.model_name}"
    elif BedrockModelProvider.is_enabled():
        crewai_llm_name = f"bedrock/{llm.metadata.model_name}"
    else:
        raise ValueError("Model not supported")
    return crewai_llm_name


class PlannerTaskOutput(BaseModel):
    """
    The output of the planner agent.
    """

    use_retrieval: bool = Field(
        ..., description="Whether to use retrieval or answer directly."
    )
    explanation: str = Field(
        ..., description="Explanation for the decision made by the planner agent."
    )

    class Config:
        schema_extra = {
            "example": {
                "use_retrieval": True,
                "explanation": "The query is related to the content described in the knowledge base summary.",
            }
        }


class PlannerAgent:
    """
    A planner agent that decides whether to use retrieval or answer directly.
    """

    def __init__(self, llm: LLM, configuration: QueryConfiguration):
        """
        Initialize the planner agent.

        Args:
            llm: The language model to use for planning.
            configuration: The query configuration.
        """
        self.llm = llm
        self.configuration = configuration

    def decide_retrieval_strategy(
        self,
        query: str,
        chat_messages: list[ChatMessage],
        data_source_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Decide whether to use retrieval or answer directly.

        Args:
            query: The user query.
            chat_messages: The chat history.
            data_source_summary: A summary of the data source content to help determine relevance.

        Returns:
            A dictionary with the decision and explanation.
        """

        # Create a planner agent using CrewAI
        planner = Agent(
            role="Planner",
            goal="Decide whether to use retrieval or answer directly",
            backstory="You are an expert planner who decides the most efficient way to answer a query.",
            llm=get_crewai_llm_object_direct(self.llm, self.configuration.model_name),
            # verbose=True,
        )

        # Define the planning task
        data_source_info = ""
        additional_data_source_questions = ""
        chat_history = ""
        if chat_messages:
            chat_history = "\n".join(
                [f"{message.role}: {message.content}" for message in chat_messages]
            )
        if data_source_summary:
            data_source_info = f"""
            ==================================================================
            Knowledge Base Summary:\n{data_source_summary}
            ==================================================================
            Chat History:\n{chat_history}
            ==================================================================
            """
            additional_data_source_questions = """
            Consider the following factors:
                1. Is the query related to the content described in the knowledge base summary?
                2. Does the knowledge base likely contain information that would help answer this query?
                3. Consider the chat history when answering the above questions.
            """

        planning_task = Task(
            description=f"""
            Analyze the following query and decide whether to use retrieval or answer directly:

            Query: {query}
            {data_source_info}

            {additional_data_source_questions}
            
            If the query is related to the content described or is in the knowledge base summary, use the retrieval strategy.
            Else, use the direct answer strategy. If the query can be answered directly based on the chat history, use the direct answer strategy.
            If there is no knowledge base summary, use the retrieval strategy first.
            """,
            agent=planner,
            expected_output="A JSON object with the decision and explanation",
            output_json=PlannerTaskOutput,
        )

        # Create a crew with just the planner agent
        crew = Crew(
            agents=[planner],
            tasks=[planning_task],
            # verbose=True,
            process=Process.sequential,
            name="PlannerAgentCrew",
            # task_callback=lambda task: logger.info(f"Task '{task=}'"),
        )

        # Run the crew to get the decision
        result = crew.kickoff()
        logger.info(f"Planner agent result: {result}")

        try:
            if result.json_dict:
                # If the result is already a JSON object, return it
                return result.json_dict
            import json
            import re

            # The result might be a string containing JSON, so we need to parse it
            # Look for JSON pattern in the result
            json_pattern = r"({.*?})"
            json_match = re.search(json_pattern, str(result), re.DOTALL)

            if json_match:
                decision_json: dict[str, Any] = json.loads(json_match.group(1))
                return decision_json
            else:
                # If no JSON pattern found, make a default decision
                logger.warning(
                    "Could not parse JSON from planner result, using default decision"
                )
                return {
                    "use_retrieval": True,
                    "explanation": "Default decision due to parsing error",
                }
        except Exception as e:
            logger.error(f"Error parsing planner result: {e}")
            # Default to using retrieval in case of error
            return {
                "use_retrieval": True,
                "explanation": f"Default decision due to error: {str(e)}",
            }
