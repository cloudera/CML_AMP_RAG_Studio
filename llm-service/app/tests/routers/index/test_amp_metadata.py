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

"""Integration tests for app/routers/index/amp_metadata/."""
from typing import Generator, Any
from unittest.mock import patch, mock_open, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.services.models import CAIIModelProvider


@pytest.fixture()
def mock_json_dump() -> Generator[Any, None, None]:
    with patch("json.dump") as mock:
        yield mock


@pytest.fixture()
def mock_file() -> Generator[Any, None, None]:
    with patch("builtins.open", new_callable=mock_open()) as m:
        yield m


class TestAmpMetadata:
    @pytest.fixture(autouse=True)
    def list_caii_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkey patch fetching CAII models."""
        monkeypatch.setattr(CAIIModelProvider, "list_llm_models", lambda: [])

    @staticmethod
    def test_save_auth_token(
        client: TestClient, mock_json_dump: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test POST /amp/config/auth-token."""
        test_token = "test_auth_token_value"

        response = client.post(
            "/amp/config/cdp-auth-token",
            json={"auth_token": test_token},
        )

        assert response.status_code == 200
        assert response.json() == "Auth token saved successfully"

        # Verify the file was opened correctly
        mock_file.assert_called_once_with("cdp_token", "w")

        # Verify the correct data was written to the file
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        assert args[0] == {"access_token": test_token}
        # todo: verify the file content
        # assert args[1] == mock_file()
