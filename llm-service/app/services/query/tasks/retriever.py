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

from queue import Queue

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel

from app.services.query.crew_events import CrewEvent, step_callback


class RetrieverResult(BaseModel):
    node_id: str | None = None
    score: float | None = None
    content: str | None = None


class RetrieverOutput(BaseModel):
    retriever_results: list[RetrieverResult]


def build_retriever_task(
    agent: Agent,
    query: str,
    chat_history: str,
    retriever_task_context: list[Task],
    retriever_tool: BaseTool,
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    retriever_task = Task(
        name="RetrieverTask",
        description="Retrieve relevant information from the index based on the user's question.\n\n"
        f"<Chat history>:\n{chat_history}\n\n<Question>:\n{query}\n\n"
        "If the question can be answered using the chat history or the context, do not use the retriever tool and "
        "return blank strings for the retriever results. If needed, use the chat history to refine the user's question "
        "to pass as input to the retriever tool.",
        agent=agent,
        tools=[retriever_tool],
        context=retriever_task_context if retriever_task_context else None,
        expected_output="Relevant information retrieved from the index.",
        output_json=RetrieverOutput,
        callback=lambda output: step_callback(
            output, "Retrieval Complete", crew_events_queue
        ),
    )
    return retriever_task
