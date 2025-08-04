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

import pytest
from unittest.mock import patch, AsyncMock, Mock

from llama_index.core.base.response.schema import Response, PydanticResponse
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.evaluation import EvaluationResult
from llama_index.core.llms import LLM
from llama_index.core.schema import NodeWithScore

from app.services.evaluators import evaluate_response, _async_evaluate_response, _build_response_object, _evaluate_faithfulness, _evaluate_relevancy

# Constants for mocking
MOCK_QUERY = "What is the capital of France?"
MOCK_RESPONSE_TEXT = "The capital of France is Paris."
MOCK_MODEL_NAME = "test-model"


@pytest.fixture
def mock_llm() -> Mock:
    """Provides a generic mock LLM object."""
    return Mock(spec=LLM)


@pytest.fixture
def mock_agent_chat_response() -> AgentChatResponse:
    """Provides a mock AgentChatResponse object for testing."""
    mock_node = Mock(spec=NodeWithScore)
    return AgentChatResponse(
        response=MOCK_RESPONSE_TEXT,
        source_nodes=[mock_node],
        metadata={"some": "metadata"},
    )


@pytest.fixture
def mock_empty_response() -> AgentChatResponse:
    """Provides a mock AgentChatResponse object with an empty response text."""
    mock_node = Mock(spec=NodeWithScore)
    return AgentChatResponse(
        response="",
        source_nodes=[mock_node],
        metadata={"some": "metadata"},
    )


@pytest.fixture
def mock_response_object(mock_agent_chat_response: AgentChatResponse) -> Response:
    """Provides a mock LlamaIndex Response object."""
    return Response(
        response=mock_agent_chat_response.response,
        source_nodes=mock_agent_chat_response.source_nodes,
        metadata=mock_agent_chat_response.metadata,
    )


@patch("app.services.evaluators.asyncio.run")
@patch("app.services.evaluators.models.LLM.get")
def test_evaluate_response_sync_wrapper(mock_get_llm: Mock, mock_asyncio_run: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that the main synchronous wrapper `evaluate_response` correctly
    fetches the LLM and calls the async runner.
    """
    # Arrange
    mock_get_llm.return_value = mock_llm
    expected_result = (0.9, 0.8)
    mock_asyncio_run.return_value = expected_result

    # Act
    result = evaluate_response(MOCK_QUERY, mock_agent_chat_response, MOCK_MODEL_NAME)

    # Assert
    mock_get_llm.assert_called_once_with(MOCK_MODEL_NAME)

    # Verifies that asyncio.run was called with the correct coroutine and that the
    # coroutine itself was created with the correct arguments.
    # The coroutine object is the single positional argument passed to asyncio.run.
    coroutine = mock_asyncio_run.call_args.args[0]

    # Inspect the coroutine to verify it's the right function with the right arguments.
    assert coroutine.__name__ == "_async_evaluate_response"
    frame_locals = coroutine.cr_frame.f_locals
    assert frame_locals["query"] == MOCK_QUERY
    assert frame_locals["chat_response"] == mock_agent_chat_response
    assert frame_locals["evaluator_llm"] == mock_llm
    assert result == expected_result


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_concurrent_and_success(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` calls evaluators concurrently and returns their scores.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=1.0)
    mock_faithfulness_eval.return_value = EvaluationResult(score=0.75)

    # Act
    relevancy, faithfulness = await _async_evaluate_response(MOCK_QUERY, mock_agent_chat_response, mock_llm)

    # Assert
    assert relevancy == 1.0
    assert faithfulness == 0.75
    mock_relevancy_eval.assert_awaited_once()
    mock_faithfulness_eval.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_handles_none_faithfulness_score(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` correctly defaults a None faithfulness score to 0.0.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=1.0)
    mock_faithfulness_eval.return_value = EvaluationResult(score=None) # Simulate a failed evaluation

    # Act
    relevancy, faithfulness = await _async_evaluate_response(MOCK_QUERY, mock_agent_chat_response, mock_llm)

    # Assert
    assert relevancy == 1.0
    assert faithfulness == 0.0


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_handles_none_relevancy_score(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` correctly defaults a None relevancy score to 0.0.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=None) # Simulate a failed evaluation
    mock_faithfulness_eval.return_value = EvaluationResult(score=0.8)

    # Act
    relevancy, faithfulness = await _async_evaluate_response(MOCK_QUERY, mock_agent_chat_response, mock_llm)

    # Assert
    assert relevancy == 0.0
    assert faithfulness == 0.8


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_handles_exception_in_relevancy(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` handles an exception in the relevancy evaluation.
    """
    # Arrange
    mock_relevancy_eval.side_effect = Exception("Simulated error in relevancy evaluation")
    mock_faithfulness_eval.return_value = EvaluationResult(score=0.8)

    # Act & Assert
    with pytest.raises(Exception, match="Simulated error in relevancy evaluation"):
        await _async_evaluate_response(MOCK_QUERY, mock_agent_chat_response, mock_llm)


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_handles_exception_in_faithfulness(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` handles an exception in the faithfulness evaluation.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=0.9)
    mock_faithfulness_eval.side_effect = Exception("Simulated error in faithfulness evaluation")

    # Act & Assert
    with pytest.raises(Exception, match="Simulated error in faithfulness evaluation"):
        await _async_evaluate_response(MOCK_QUERY, mock_agent_chat_response, mock_llm)


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_with_empty_response(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_empty_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` handles an empty response text.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=0.1)  # Low score for empty response
    mock_faithfulness_eval.return_value = EvaluationResult(score=0.2)  # Low score for empty response

    # Act
    relevancy, faithfulness = await _async_evaluate_response(MOCK_QUERY, mock_empty_response, mock_llm)

    # Assert
    assert relevancy == 0.1
    assert faithfulness == 0.2
    # Verify that the evaluators were called with a Response object containing an empty response text
    # Get the first positional argument (which should be the Response object)
    response_obj_arg = mock_relevancy_eval.call_args.args[0]
    assert response_obj_arg.response == ""


@pytest.mark.asyncio
@patch("app.services.evaluators._evaluate_faithfulness", new_callable=AsyncMock)
@patch("app.services.evaluators._evaluate_relevancy", new_callable=AsyncMock)
async def test_async_evaluate_response_with_empty_query(mock_relevancy_eval: Mock, mock_faithfulness_eval: Mock, mock_agent_chat_response: Mock, mock_llm: Mock) -> None:
    """
    Tests that `_async_evaluate_response` handles an empty query.
    """
    # Arrange
    mock_relevancy_eval.return_value = EvaluationResult(score=0.3)  # Low score for empty query
    mock_faithfulness_eval.return_value = EvaluationResult(score=0.4)  # Low score for empty query
    empty_query = ""

    # Act
    relevancy, faithfulness = await _async_evaluate_response(empty_query, mock_agent_chat_response, mock_llm)

    # Assert
    assert relevancy == 0.3
    assert faithfulness == 0.4
    # Verify that the evaluators were called with an empty query
    # The query is passed to the _evaluate_relevancy and _evaluate_faithfulness functions
    # which then pass it to the evaluator's aevaluate_response method
    # We can verify this by checking the call to _async_evaluate_response
    assert mock_relevancy_eval.call_args.args[2] == ""  # Third positional arg is query
    assert mock_faithfulness_eval.call_args.args[2] == ""  # Third positional arg is query


def test_build_response_object(mock_agent_chat_response: Mock) -> None:
    """
    Tests the helper function that converts an AgentChatResponse to a Response.
    """
    # Act
    response_obj = _build_response_object(mock_agent_chat_response)

    # Assert
    assert isinstance(response_obj, Response)
    assert not isinstance(response_obj, PydanticResponse) # Ensure it's the base class
    assert response_obj.response == MOCK_RESPONSE_TEXT
    assert response_obj.source_nodes == mock_agent_chat_response.source_nodes
    assert response_obj.metadata == mock_agent_chat_response.metadata


@pytest.mark.asyncio
@patch("app.services.evaluators.FaithfulnessEvaluator")
async def test_evaluate_faithfulness_helper(mock_faithfulness_evaluator: Mock, mock_response_object: Mock, mock_llm: Mock) -> None:
    """Tests that the faithfulness helper initializes and calls the evaluator correctly."""
    # Arrange
    mock_evaluator_instance = Mock()
    mock_evaluator_instance.aevaluate_response = AsyncMock()
    mock_faithfulness_evaluator.return_value = mock_evaluator_instance

    # Act
    await _evaluate_faithfulness(mock_response_object, mock_llm, MOCK_QUERY)

    # Assert
    mock_faithfulness_evaluator.assert_called_once_with(llm=mock_llm)
    mock_evaluator_instance.aevaluate_response.assert_awaited_once_with(query=MOCK_QUERY, response=mock_response_object)


@pytest.mark.asyncio
@patch("app.services.evaluators.RelevancyEvaluator")
async def test_evaluate_relevancy_helper(mock_relevancy_evaluator: Mock, mock_response_object: Mock, mock_llm: Mock) -> None:
    """Tests that the relevancy helper initializes and calls the evaluator correctly."""
    # Arrange
    mock_evaluator_instance = Mock()
    mock_evaluator_instance.aevaluate_response = AsyncMock()
    mock_relevancy_evaluator.return_value = mock_evaluator_instance

    # Act
    await _evaluate_relevancy(mock_response_object, mock_llm, MOCK_QUERY)

    # Assert
    mock_relevancy_evaluator.assert_called_once_with(llm=mock_llm)
    mock_evaluator_instance.aevaluate_response.assert_awaited_once_with(query=MOCK_QUERY, response=mock_response_object)
