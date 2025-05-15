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

from crewai import Agent, Task
from crewai_tools.tools.serper_dev_tool.serper_dev_tool import SerperDevTool

from app.services.query.agents.date_tool import DateTool


def build_calculator_agent(crewai_llm_name):
    calculator = Agent(
        role="Calculator",
        goal="Perform accurate mathematical calculations based on research findings",
        backstory="You are an expert mathematician who can perform complex calculations and data analysis.",
        llm=crewai_llm_name,
        # verbose=True,
        # callbacks=[pause],
    )
    calculation_task = Task(
        name="CalculatorTask",
        description="Perform any necessary calculations based on the research findings. If the query requires numerical analysis, perform the calculations and show your work. If no calculations are needed, simply state that no calculations are required.",
        agent=calculator,
        expected_output="Results of any calculations performed, with step-by-step workings",
        # callback=pause,
    )
    return calculation_task, calculator


def build_search_agent(crewai_llm_name, date_tool):
    serper = SerperDevTool()
    searcher = Agent(
        role="Search Agent",
        goal="Search the internet for relevant information",
        backstory="You know everything about the web.  You can find anything that exists on the web.",
        llm=crewai_llm_name,
        tools=[date_tool, serper],
        verbose=True,
        # callbacks=[pause],
    )
    search_task = Task(
        name="SearchTask",
        description="Search the internet for relevant information related to the query.",
        agent=searcher,
        # tools=[date_tool],
        expected_output="Results of any search performed, with step-by-step workings",
        # callback=pause,
    )
    return search_task, searcher, serper


def build_date_agent(crewai_llm):
    date_tool = DateTool()
    date_finder = Agent(
        role="DateFinder",
        goal="Find the current date and time",
        backstory="You are an expert at finding the current date and time.",
        llm=crewai_llm,
        tools=[date_tool],
        # verbose=True,
        # callbacks=[pause],
    )
    date_task = Task(
        name="DateFinderTask",
        description="Find the current date and time.",
        agent=date_finder,
        expected_output="The current date and time.",
        # tools=[date_tool],
        # async_execution=True,
        # callback=pause,
    )
    return date_finder, date_task, date_tool
