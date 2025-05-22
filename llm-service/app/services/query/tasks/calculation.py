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

from app.services.query.crew_events import CrewEvent, step_callback


def build_calculation_task(
    agent: Agent,
    calculation_task_context: list[Task],
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    """
    Build a calculation task for the agent.
    This task will perform any necessary calculations based on the research findings.

    Args:
        agent (Agent): The agent that will perform the calculations.
        calculation_task_context (list[Task]): The list of Task objects that will be used as context for the calculation task.
        crew_events_queue (Queue[CrewEvent]): The queue to send events to.

    Returns:
        Task: The calculation task.
    """
    calculation_task = Task(
        name="CalculatorTask",
        description="Perform any necessary calculations based on the research findings. If the query requires numerical analysis, perform the calculations and show your work. If no calculations are needed, simply state that no calculations are required.",
        agent=agent,
        context=calculation_task_context if calculation_task_context else None,
        expected_output="Results of any calculations performed, with step-by-step workings",
        callback=lambda output: step_callback(
            output, "Calculation Complete", crew_events_queue
        ),
    )
    return calculation_task
