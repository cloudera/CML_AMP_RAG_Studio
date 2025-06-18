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
import logging
from typing import Optional

from . import models
from .chat_history.chat_history_manager import (
    chat_history_manager,
    RagStudioChatMessage,
)
from .metadata_apis import session_metadata_api

logger = logging.getLogger(__name__)

RENAME_SESSION_PROMPT_TEMPLATE = """
You are tasked with suggesting an apt name for a chat session based on its first interaction between a User and an Assistant. 

# Instructions
IMPORTANTLY, ONLY RETURN THE NAME OF THE SESSION.  Only return a single line and sessions name, without any additional text or formatting.
Use the below interactions as a guide but do not include them in your response.

### Example 1:
First Interaction:
```
User: What is your name?
Assistant: My name is Assistant.
```

Session Name:
Introduction

### Example 2:
First Interaction:
```
User: What do you know about the Moon?
Assistant: The Moon is Earth's only natural satellite. It is the fifth-largest satellite in the Solar System, and by far the largest among planetary satellites relative to the size of the planet that it orbits.
```

Session Name:
Facts about the Moon

# Your turn:
First Interaction:
```
User: {}
Assistant: {}
```

Session Name: 
"""


def rename_session(session_id: int, user_name: Optional[str]) -> str:
    chat_history: list[RagStudioChatMessage] = (
        chat_history_manager.retrieve_chat_history(session_id=session_id)
    )
    if not chat_history:
        logger.info("No chat history found for session ID %s", session_id)
        return ""
    first_interaction = chat_history[0].rag_message
    session_metadata = session_metadata_api.get_session(session_id, user_name)
    llm = models.LLM.get(session_metadata.inference_model)
    prompt = RENAME_SESSION_PROMPT_TEMPLATE.format(
        first_interaction.user,
        first_interaction.assistant,
    )
    response = llm.complete(prompt=prompt)
    session_name = response.text.strip().split("\n")[0]
    session_metadata.name = session_name
    updated_session = session_metadata_api.update_session(session_metadata, user_name)
    return updated_session.name
