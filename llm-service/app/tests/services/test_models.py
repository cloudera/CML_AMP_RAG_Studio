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
import pytest

from app.config import MODEL_PROVIDER_ENV_VAR_NAME
from app.services import models
from app.services.caii import caii
from app.services.caii.types import ListEndpointEntry
from app.services.models.providers import BedrockModelProvider
from app.services.models.providers._model_provider import (
    _ModelProvider,
    get_all_env_var_names,
)


@pytest.fixture(params=_ModelProvider.__subclasses__())
def EnabledModelProvider(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> type[_ModelProvider]:
    """Sets and unsets environment variables for the given model provider."""
    ModelProviderSubcls: type[_ModelProvider] = request.param

    for name in get_all_env_var_names():
        monkeypatch.delenv(name, raising=False)
    for name in ModelProviderSubcls.get_env_var_names():
        monkeypatch.setenv(name, "test")
    monkeypatch.setenv(
        MODEL_PROVIDER_ENV_VAR_NAME,
        ModelProviderSubcls.get_model_source(),
    )

    return ModelProviderSubcls


class TestListAvailableModels:
    @pytest.fixture(autouse=True)
    def caii_get_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkey patch fetching models from CAII."""
        endpoints: list[ListEndpointEntry] = []
        for namespace in ["test-namespace-1, test-namespace-2"]:
            for name in ["test-model-1", "test-model-2"]:
                endpoints.append(
                    ListEndpointEntry(
                        namespace=namespace,
                        name=name,
                        model_name=f"ragtime/{name}",
                        url=f"https://this.is.test/namespaces/{namespace}/endpoints/{name}/v1/test",
                        state="Loaded",
                        task="TEST",
                    )
                )

        monkeypatch.setattr(caii, "get_models_with_task", lambda task_type: endpoints)

    @pytest.fixture(autouse=True)
    def get_foundation_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkey patch fetching foundation models."""
        monkeypatch.setattr(
            BedrockModelProvider, "get_foundation_models", lambda modality: []
        )

    def test_embedding(self, EnabledModelProvider: type[_ModelProvider]) -> None:
        """Verify models.Embedding.list_available() only returns models from the enabled model provider."""
        assert (
            models.Embedding.list_available()
            == EnabledModelProvider.list_embedding_models()
        )

    def test_llm(self, EnabledModelProvider: type[_ModelProvider]) -> None:
        """Verify models.LLM.list_available() only returns models from the enabled model provider."""
        assert models.LLM.list_available() == EnabledModelProvider.list_llm_models()

    def test_reranking(self, EnabledModelProvider: type[_ModelProvider]) -> None:
        """Verify models.Reranking.list_available() only returns models from the enabled model provider."""
        assert (
            models.Reranking.list_available()
            == EnabledModelProvider.list_reranking_models()
        )
