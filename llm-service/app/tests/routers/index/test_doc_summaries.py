import time
start_time = time.time()
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
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from ...conftest import BotoObject


class TestDocumentSummaries:
    @staticmethod
    def test_generate_summary(
        client: TestClient,
        index_document_request_body: dict[str, Any],
        data_source_id: int,
        document_id: str,
        s3_object: BotoObject,
        test_file: Path,
    ) -> None:
        response = client.post(
            f"/data_sources/{data_source_id}/documents/{document_id}/index",
            json=index_document_request_body,
        )

        assert response.status_code == 200

        post_summarization_response = client.post(
            f"/data_sources/{data_source_id}/documents/{document_id}/summary",
            json={
                "s3_bucket_name": s3_object.bucket_name,
                "s3_document_key": s3_object.key,
                "original_filename": "test.txt",
            },
        )

        assert post_summarization_response.status_code == 200
        assert post_summarization_response.text == '"this is a completion response"'

        get_summary_response = client.get(
            f"/data_sources/{data_source_id}/documents/{document_id}/summary"
        )

        assert get_summary_response.status_code == 200
        assert get_summary_response.text == '"this is a completion response"'

        get_data_source_response = client.get(f"/data_sources/{data_source_id}/summary")
        assert get_data_source_response.status_code == 200
        # our monkeypatched model always returns this.
        # todo: Figure out how to parameterize the monkey patch
        assert get_data_source_response.text == '"this is a completion response"'

    @staticmethod
    def test_delete_document(
        client: TestClient,
        index_document_request_body: dict[str, Any],
        data_source_id: int,
        document_id: str,
        s3_object: BotoObject,
        test_file: Path,
    ) -> None:
        response = client.post(
            f"/data_sources/{data_source_id}/documents/{document_id}/index",
            json=index_document_request_body,
        )

        assert response.status_code == 200

        post_summarization_response = client.post(
            f"/data_sources/{data_source_id}/documents/{document_id}/summary",
            json={
                "s3_bucket_name": s3_object.bucket_name,
                "s3_document_key": s3_object.key,
                "original_filename": "test.txt",
            },
        )

        assert post_summarization_response.status_code == 200

        delete_document_response = client.delete(
            f"/data_sources/{data_source_id}/documents/{document_id}"
        )

        assert delete_document_response.status_code == 200

        get_summary_response = client.get(
            f"/data_sources/{data_source_id}/documents/{document_id}/summary"
        )

        assert get_summary_response.text == '"No summary found for this document."'
        assert get_summary_response.status_code == 200

print('tests/routers/index/test_doc_summaries.py took {time.time() - start_time} seconds to import')
