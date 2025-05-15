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

from crewai import Agent, Task, Crew, Process

from app.services.query.agents.agents import (
    build_date_agent,
    build_calculator_agent,
    build_search_agent,
)
from app.services.query.agents.models import get_crewai_llm_object_direct


def query_crew(llm, configuration, query_str, context, chat_history):
    crewai_llm = get_crewai_llm_object_direct(llm, configuration.model_name)

    # Define tasks for the agents
    date_finder, date_task, date_tool = build_date_agent(crewai_llm)
    calculation_task, calculator = build_calculator_agent(crewai_llm)

    search_task, searcher, serper = None, None, None
    if "search" in configuration.tools:
        search_task, searcher, serper = build_search_agent(crewai_llm, date_tool)

    research_tools = [date_tool]
    if serper:
        research_tools.append(serper)

    researcher = Agent(
        role="Researcher",
        goal="Find the most accurate and relevant information",
        backstory="You are an expert researcher who provides accurate and relevant information based on the provided context.",
        llm=crewai_llm,
        # verbose=True,
        tools=research_tools,
        # callbacks=[pause],
    )
    research_task = Task(
        name="ResearcherTask",
        description=f"Research the following query using any provided context and chat history: {query_str}\n\nContext: {context} \n\nChat history: {chat_history}",
        agent=researcher,
        expected_output="A detailed analysis of the query based on the provided context",
        # tools=[date_tool, serper],
        # context=[search_task, date_task],
        # callback=pause,
    )

    # Create a responder agent that formulates the final response
    responder = Agent(
        role="Responder",
        goal="Provide a comprehensive and accurate response to the query",
        backstory="You are an expert at formulating clear, concise, and accurate responses based on research findings.",
        llm=crewai_llm,
        # callbacks=[pause],
        # verbose=True,
    )

    response_task = Task(
        name="ResponderTask",
        description="Formulate a comprehensive response based on the research findings and calculations",
        agent=responder,
        expected_output="A comprehensive and accurate response to the query",
        # context=[search_task, date_task, research_task, calculation_task],
        # callback=pause,
    )

    # Create a crew with the agents and tasks
    agents = [date_finder]
    tasks = [date_task]
    if searcher:
        agents.append(searcher)
        tasks.append(search_task)
    agents.extend([researcher, calculator, responder])
    tasks.extend([research_task, calculation_task, response_task])

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        name="QueryCrew",
        # task_callback=pause,
    )
