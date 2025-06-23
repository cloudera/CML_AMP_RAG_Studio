from typing import (
    Sequence,
    Optional,
    Union,
    Any,
    List,
    AsyncGenerator,
)

from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
)
from llama_index.core.tools import BaseTool
from llama_index.llms.bedrock_converse import BedrockConverse


class FakeStreamBedrockConverse(BedrockConverse):
    """
    A class that inherits from BedrockConverse but overrides its astream_chat_with_tools function.
    This class is used to create a non-streaming version of the BedrockConverse.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the FakeStreamBedrockConverse class.
        """
        super().__init__(*args, **kwargs)

    async def astream_chat_with_tools(
        self,
        tools: Sequence["BaseTool"],
        user_msg: Optional[Union[str, ChatMessage]] = None,
        chat_history: Optional[List[ChatMessage]] = None,
        verbose: bool = False,
        allow_parallel_tool_calls: bool = False,
        tool_required: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[ChatResponse, None]:
        # This method is overridden to provide a non-streaming version of the chat with tools.
        # Here we yield a single ChatResponse object instead of streaming multiple responses.
        async def _fake_stream() -> AsyncGenerator[ChatResponse, None]:
            response = await self.achat_with_tools(
                tools=tools,
                user_msg=user_msg,
                chat_history=chat_history,
                verbose=verbose,
                allow_parallel_tool_calls=allow_parallel_tool_calls,
                tool_required=tool_required,
                **kwargs,
            )
            yield response

        return _fake_stream()

    @classmethod
    def from_bedrock_converse(
        cls, bedrock_converse: BedrockConverse
    ) -> "FakeStreamBedrockConverse":
        """
        Create a FakeStreamBedrockConverse object from a BedrockConverse object.

        Args:
            bedrock_converse: A BedrockConverse object

        Returns:
            A FakeStreamBedrockConverse object with the same public attributes as the input BedrockConverse
        """
        # Create a new instance of FakeStreamBedrockConverse with only the public parameters
        # Let the parent class handle initialization of private attributes
        return cls(
            model=bedrock_converse.model,
            temperature=bedrock_converse.temperature,
            max_tokens=bedrock_converse.max_tokens,
            additional_kwargs=bedrock_converse.additional_kwargs,
            callback_manager=bedrock_converse.callback_manager,
            system_prompt=bedrock_converse.system_prompt,
            messages_to_prompt=bedrock_converse.messages_to_prompt,
            completion_to_prompt=bedrock_converse.completion_to_prompt,
            pydantic_program_mode=bedrock_converse.pydantic_program_mode,
            output_parser=bedrock_converse.output_parser,
            profile_name=bedrock_converse.profile_name,
            aws_access_key_id=bedrock_converse.aws_access_key_id,
            aws_secret_access_key=bedrock_converse.aws_secret_access_key,
            aws_session_token=bedrock_converse.aws_session_token,
            region_name=bedrock_converse.region_name,
            api_version=bedrock_converse.api_version,
            use_ssl=bedrock_converse.use_ssl,
            verify=bedrock_converse.verify,
            endpoint_url=bedrock_converse.endpoint_url,
            timeout=bedrock_converse.timeout,
            max_retries=bedrock_converse.max_retries,
            guardrail_identifier=bedrock_converse.guardrail_identifier,
            guardrail_version=bedrock_converse.guardrail_version,
            application_inference_profile_arn=bedrock_converse.application_inference_profile_arn,
            trace=bedrock_converse.trace,
        )
