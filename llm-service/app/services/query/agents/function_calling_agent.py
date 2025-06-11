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
import uuid
from functools import partial
from typing import Optional, Any, List, Union, Dict

from llama_index.agent.openai.base import DEFAULT_MAX_FUNCTION_CALLS
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.agent.function_calling import FunctionCallingAgent
from llama_index.core.agent.runner.base import AgentState
from llama_index.core.agent.utils import add_user_step_to_memory
from llama_index.core.base.agent.types import TaskStep, TaskStepOutput, Task
from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.callbacks import trace_method, CallbackManager
from llama_index.core.chat_engine.types import (
    AgentChatResponse,
    StreamingAgentChatResponse,
    AGENT_CHAT_RESPONSE_TYPE,
    ChatResponseMode,
)
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.memory import BaseMemory
from llama_index.core.objects import ObjectRetriever
from llama_index.core.tools import BaseTool, ToolOutput
from llama_index.core.types import Thread


class FunctionCallingAgentWithStreamer(FunctionCallingAgent):
    @classmethod
    def from_tools(
        cls,
        tools: Optional[List[BaseTool]] = None,
        tool_retriever: Optional[ObjectRetriever[BaseTool]] = None,
        llm: Optional[FunctionCallingLLM] = None,
        verbose: bool = False,
        max_function_calls: int = DEFAULT_MAX_FUNCTION_CALLS,
        callback_manager: Optional[CallbackManager] = None,
        system_prompt: Optional[str] = None,
        prefix_messages: Optional[List[ChatMessage]] = None,
        memory: Optional[BaseMemory] = None,
        chat_history: Optional[List[ChatMessage]] = None,
        state: Optional[AgentState] = None,
        allow_parallel_tool_calls: bool = True,
        **kwargs: Any,
    ) -> "FunctionCallingAgentWithStreamer":
        """Create a FunctionCallingAgent from a list of tools."""
        tools = tools or []

        llm = llm or Settings.llm  # type: ignore
        assert isinstance(
            llm, FunctionCallingLLM
        ), "llm must be an instance of FunctionCallingLLM"

        if callback_manager is not None:
            llm.callback_manager = callback_manager

        if system_prompt is not None:
            if prefix_messages is not None:
                raise ValueError(
                    "Cannot specify both system_prompt and prefix_messages"
                )
            prefix_messages = [ChatMessage(content=system_prompt, role="system")]

        prefix_messages = prefix_messages or []

        agent_worker = FunctionCallingAgentWithStreamerWorker.from_tools(
            tools,
            tool_retriever=tool_retriever,
            llm=llm,
            verbose=verbose,
            max_function_calls=max_function_calls,
            callback_manager=callback_manager,
            prefix_messages=prefix_messages,
            allow_parallel_tool_calls=allow_parallel_tool_calls,
        )

        return cls(
            agent_worker=agent_worker,
            memory=memory,
            chat_history=chat_history,
            state=state,
            llm=llm,
            callback_manager=callback_manager,
            verbose=verbose,
            **kwargs,
        )


class FunctionCallingAgentWithStreamerWorker(FunctionCallingAgentWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _process_message(self, task, chat_response):
        ai_message = chat_response.message
        task.extra_state["new_memory"].put(ai_message)
        return AgentChatResponse(
            response=str(ai_message.content),
            sources=task.extra_state["sources"],
        )

    def _get_stream_ai_response(
        self, task: Task, **llm_chat_kwargs: Any
    ) -> StreamingAgentChatResponse:
        chat_stream_response = StreamingAgentChatResponse(
            chat_stream=self._llm.stream_chat(**llm_chat_kwargs),
            sources=task.extra_state["sources"],
        )
        # Get the response in a separate thread so we can yield the response
        thread = Thread(
            target=chat_stream_response.write_response_to_history,
            args=(task.extra_state["new_memory"],),
            kwargs={"on_stream_end_fn": partial(self.finalize_task, task)},
        )
        thread.start()
        # Wait for the event to be set
        chat_stream_response.is_function_not_none_thread_event.wait()
        # If it is executing an openAI function, wait for the thread to finish
        if chat_stream_response.is_function:
            thread.join()

        # if it's false, return the answer (to stream)
        return chat_stream_response

    async def _get_async_stream_ai_response(
        self, task: Task, **llm_chat_kwargs: Any
    ) -> StreamingAgentChatResponse:
        chat_stream_response = StreamingAgentChatResponse(
            achat_stream=await self._llm.astream_chat(**llm_chat_kwargs),
            sources=task.extra_state["sources"],
        )
        # create task to write chat response to history
        chat_stream_response.awrite_response_to_history_task = asyncio.create_task(
            chat_stream_response.awrite_response_to_history(
                task.extra_state["new_memory"],
                on_stream_end_fn=partial(self.afinalize_task, task),
            )
        )
        chat_stream_response._ensure_async_setup()

        # wait until openAI functions stop executing
        await chat_stream_response.is_function_false_event.wait()

        # return response stream
        return chat_stream_response

    def _get_agent_response(
        self, task: Task, mode: ChatResponseMode, **llm_chat_kwargs: Any
    ) -> AGENT_CHAT_RESPONSE_TYPE:
        if mode == ChatResponseMode.WAIT:
            chat_response: ChatResponse = self._llm.chat(**llm_chat_kwargs)
            return self._process_message(task, chat_response)
        elif mode == ChatResponseMode.STREAM:
            return self._get_stream_ai_response(task, **llm_chat_kwargs)
        else:
            raise NotImplementedError

    async def _get_async_agent_response(
        self, task: Task, mode: ChatResponseMode, **llm_chat_kwargs: Any
    ) -> AGENT_CHAT_RESPONSE_TYPE:
        if mode == ChatResponseMode.WAIT:
            chat_response: ChatResponse = await self._llm.achat(**llm_chat_kwargs)
            return self._process_message(task, chat_response)
        elif mode == ChatResponseMode.STREAM:
            return await self._get_async_stream_ai_response(task, **llm_chat_kwargs)
        else:
            raise NotImplementedError

    def _get_llm_chat_kwargs(
        self,
        task: Task,
        tools: Optional[List[BaseTool]] = None,
        tool_choice: Union[str, dict] = "auto",
    ) -> Dict[str, Any]:
        llm_chat_kwargs: dict = {"messages": self.get_all_messages(task)}
        return llm_chat_kwargs

    @trace_method("run_step")
    def run_step(self, step: TaskStep, task: Task, **kwargs: Any) -> TaskStepOutput:
        """Run step."""
        if step.input is not None:
            add_user_step_to_memory(
                step, task.extra_state["new_memory"], verbose=self._verbose
            )
        # TODO: see if we want to do step-based inputs
        tools = self.get_tools(task.input)

        # get response and tool call (if exists)
        response = self._llm.chat_with_tools(
            tools=tools,
            user_msg=None,
            chat_history=self.get_all_messages(task),
            verbose=self._verbose,
            allow_parallel_tool_calls=self.allow_parallel_tool_calls,
        )
        tool_calls = self._llm.get_tool_calls_from_response(
            response, error_on_no_tool_call=False
        )
        tool_outputs: List[ToolOutput] = []

        if self._verbose and response.message.content:
            print("=== LLM Response ===")
            print(str(response.message.content))

        if not self.allow_parallel_tool_calls and len(tool_calls) > 1:
            raise ValueError(
                "Parallel tool calls not supported for synchronous function calling agent"
            )

        # call all tools, gather responses
        task.extra_state["new_memory"].put(response.message)
        if (
            len(tool_calls) == 0
            or task.extra_state["n_function_calls"] >= self._max_function_calls
        ):
            # we are done
            is_done = True
            new_steps = []
        else:
            is_done = False
            for i, tool_call in enumerate(tool_calls):
                # TODO: maybe execute this with multi-threading
                return_direct = self._call_function(
                    tools,
                    tool_call,
                    task.extra_state["new_memory"],
                    tool_outputs,
                    verbose=self._verbose,
                )
                task.extra_state["sources"].append(tool_outputs[-1])
                task.extra_state["n_function_calls"] += 1

                # check if any of the tools return directly -- only works if there is one tool call
                if i == 0 and return_direct:
                    is_done = True
                    response = task.extra_state["sources"][-1].content
                    break

            # put tool output in sources and memory
            new_steps = (
                [
                    step.get_next_step(
                        step_id=str(uuid.uuid4()),
                        # NOTE: input is unused
                        input=None,
                    )
                ]
                if not is_done
                else []
            )

        # get response string
        # return_direct can change the response type
        try:
            response_str = str(response.message.content)
        except AttributeError:
            response_str = str(response)

        agent_response = StreamingAgentChatResponse(
            response=response_str, sources=tool_outputs
        )

        return TaskStepOutput(
            output=agent_response,
            task_step=step,
            is_last=is_done,
            next_steps=new_steps,
        )

    @trace_method("run_step")
    def stream_step(self, step: TaskStep, task: Task, **kwargs: Any) -> TaskStepOutput:
        output = self.run_step(
            task=task,
            step=step,
            **kwargs,
        )
        return output

    @trace_method("run_step")
    async def astream_step(
        self, step: TaskStep, task: Task, **kwargs: Any
    ) -> TaskStepOutput:
        output = await self.arun_step(
            task=task,
            step=step,
            **kwargs,
        )
        return output
