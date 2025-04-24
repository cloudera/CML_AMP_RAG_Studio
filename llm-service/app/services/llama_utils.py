import time
start_time = time.time()
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

from typing import List, Optional, Sequence

from llama_index.core.base.llms.types import ChatMessage, MessageRole

BOS, EOS = "<|begin_of_text|>", "<|end_of_text|>"
EOT = "<|eot_id|>"
SH, EH = "<|start_header_id|>", "<|end_header_id|>"
DEFAULT_SYSTEM_PROMPT = """\
You are a helpful, respectful and honest assistant. \
Always answer as helpfully as possible and follow ALL given instructions. \
Do not speculate or make up information. \
Do not reference any given instructions or context. \
"""


def messages_to_prompt(
    messages: Sequence[ChatMessage], system_prompt: Optional[str] = None
) -> str:
    string_messages: List[str] = []
    if messages[0].role == MessageRole.SYSTEM:
        # pull out the system message (if it exists in messages)
        system_message_str = messages[0].content or ""
        messages = messages[1:]
    else:
        system_message_str = system_prompt or DEFAULT_SYSTEM_PROMPT

    for i in range(0, len(messages), 2):
        # first message should always be a user
        user_message = messages[i]
        assert user_message.role == MessageRole.USER
        str_message = ""
        if i == 0:
            # make sure system prompt is included at the start
            str_message = f"{BOS}{SH}system{EH}\n\n{system_message_str.strip()}{EOT}\n"
        else:
            # end previous user-assistant interaction
            string_messages[-1] += f"{EOT}\n"

        # include user message content
        str_message += (
            f"{SH}user{EH}\n\n{user_message.content}{EOT}\n{SH}assistant{EH}\n\n"
        )

        if len(messages) > (i + 1):
            # if assistant message exists, add to str_message
            assistant_message = messages[i + 1]
            assert assistant_message.role == MessageRole.ASSISTANT
            str_message += f"{assistant_message.content}"

        string_messages.append(str_message)

    result = "".join(string_messages)
    return result


def messages_to_prompt_mistral(
    messages: Sequence[ChatMessage], system_prompt: Optional[str] = None
) -> str:
    string_messages: List[str] = []
    for i in range(0, len(messages), 2):
        # first message should always be a user
        user_message = messages[i]
        assert user_message.role == MessageRole.USER
        string_messages[-1] += f"{EOT}\n"

        # include user message content
        str_message = (
            f"{SH}user{EH}\n\n{user_message.content}{EOT}\n{SH}assistant{EH}\n\n"
        )

        if len(messages) > (i + 1):
            # if assistant message exists, add to str_message
            assistant_message = messages[i + 1]
            assert assistant_message.role == MessageRole.ASSISTANT
            str_message += f"{assistant_message.content}"

        string_messages.append(str_message)

    result = "".join(string_messages)
    return result


def completion_to_prompt(completion: str, system_prompt: Optional[str] = None) -> str:
    system_prompt_str = system_prompt or DEFAULT_SYSTEM_PROMPT

    result = (
        f"{BOS}{SH}system{EH}\n\n{system_prompt_str.strip()}{EOT}\n"
        f"{SH}user{EH}\n\n{completion.strip()}{EOT}\n"
        f"{SH}assistant{EH}\n\n"
    )
    return result


def mistralv2_messages_to_prompt(messages: Sequence[ChatMessage]) -> str:
    print(f"mistralv2_messages_to_prompt: {messages}")
    conversation = ""
    bos_token = "<s>"
    eos_token = "</s>"
    if messages[0].role == MessageRole.SYSTEM:
        loop_messages = messages[1:]
        system_message = messages[0].content
    else:
        loop_messages = messages
        system_message = None

    for index, message in enumerate(loop_messages):
        if (message.role == MessageRole.USER) != (index % 2 == 0):
            raise Exception(
                "HFI Conversation roles must alternate user/assistant/user/assistant/..."
            )
        message_content: str = message.content
        if index == 0 and system_message is not None:
            content = "<<SYS>>\n" + system_message + "\n<</SYS>>\n\n" + message_content
        else:
            content = message_content
        if message.role == MessageRole.USER:
            conversation += bos_token + "[INST] " + content.strip() + " [/INST]"
        elif message.role == MessageRole.ASSISTANT:
            conversation += " " + content.strip() + " " + eos_token

    return conversation

print(f'services/llama_utils.py took {time.time() - start_time} seconds to import')
