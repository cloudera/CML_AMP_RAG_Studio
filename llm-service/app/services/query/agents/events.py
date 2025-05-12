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
import asyncio
import time
from typing import AsyncGenerator

from crewai.utilities.events import (
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
    AgentExecutionCompletedEvent,
)
from crewai.utilities.events.base_event_listener import BaseEventListener

# Global queue to store crew events
crew_events_queue = asyncio.Queue()


async def generate_queue() -> AsyncGenerator[str, None]:
    while True:
        event = await crew_events_queue.get()
        print(f"about to maybe yield event: {event}")
        if event.event_type == "crew_completed":
            break
        yield f"{event}"


class MyCustomListener(BaseEventListener):
    def __init__(self):
        super().__init__()

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event):
            print(f"Crew '{event.crew_name}' has started execution!")
            # Add event data to the queue
            event_data = {
                "event_type": "crew_started",
                "crew_name": event.crew_name,
                "timestamp": time.time(),
            }
            asyncio.run(crew_events_queue.put(event_data))

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event):
            print(f"Crew '{event.crew_name}' has completed execution!")
            print(f"Output: {event.output}")
            event_data = {
                "event_type": "crew_completed",
                "crew_name": event.crew_name,
                "timestamp": time.time(),
            }
            asyncio.run(crew_events_queue.put(event_data))

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_execution_completed(source, event: AgentExecutionCompletedEvent):
            print(f"Agent '{event.agent.role}' completed task")
            print(f"Output: {event.output}")
            event_data = {
                "event_type": "agent_execution_completed",
                "crew_name": str(event.agent.crew),
                "timestamp": time.time(),
            }
            asyncio.run(crew_events_queue.put(event_data))
