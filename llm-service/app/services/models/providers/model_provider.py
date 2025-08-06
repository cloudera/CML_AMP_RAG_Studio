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
import abc
import os

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from app.config import settings
from .._model_source import ModelSource
from ...caii.types import ModelResponse


class ModelProvider(abc.ABC):
    @classmethod
    def is_enabled(cls) -> bool:
        """Return whether this model provider is enabled, based on the presence of required env vars."""
        return all(map(os.environ.get, cls.get_env_var_names()))

    @staticmethod
    def get_provider_class() -> type["ModelProvider"]:
        """Return the ModelProvider subclass for the given provider name."""
        from . import (
            AzureModelProvider,
            CAIIModelProvider,
            OpenAiModelProvider,
            BedrockModelProvider,
        )

        model_provider = settings.model_provider
        if model_provider == "Azure":
            return AzureModelProvider
        elif model_provider == "CAII":
            return CAIIModelProvider
        elif model_provider == "OpenAI":
            return OpenAiModelProvider
        elif model_provider == "Bedrock":
            return BedrockModelProvider

        # Fallback to priority order if no specific provider is set
        if AzureModelProvider.is_enabled():
            return AzureModelProvider
        elif OpenAiModelProvider.is_enabled():
            return OpenAiModelProvider
        elif BedrockModelProvider.is_enabled():
            return BedrockModelProvider
        return CAIIModelProvider

    @staticmethod
    @abc.abstractmethod
    def get_env_var_names() -> set[str]:
        """Return the names of the env vars required by this model provider."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def list_llm_models() -> list[ModelResponse]:
        """Return names and IDs of available LLM models."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def list_embedding_models() -> list[ModelResponse]:
        """Return names and IDs of available embedding models."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def list_reranking_models() -> list[ModelResponse]:
        """Return names and IDs of available reranking models."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_llm_model(name: str) -> LLM:
        """Return LLM model with `name`."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_embedding_model(name: str) -> BaseEmbedding:
        """Return embedding model with `name`."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_reranking_model(name: str, top_n: int) -> BaseNodePostprocessor:
        """Return reranking model with `name`."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_model_source() -> ModelSource:
        raise NotImplementedError
