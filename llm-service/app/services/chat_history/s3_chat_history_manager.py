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

import json
import logging
import tempfile
from typing import List

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.services.chat_history.chat_history_manager import (
    ChatHistoryManager,
    RagStudioChatMessage,
)

logger = logging.getLogger(__name__)


class S3ChatHistoryManager(ChatHistoryManager):
    """Chat history manager that uses S3 for storage."""

    def __init__(self, bucket_name: str = settings.document_bucket):
        self.bucket_name = bucket_name
        self.bucket_prefix = settings.document_bucket_prefix
        self._s3_client = None

    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            session = boto3.session.Session()
            self._s3_client = session.client("s3")
        return self._s3_client

    def _get_s3_key(self, session_id: int) -> str:
        """Build the S3 key for a session's chat history."""
        if self.bucket_prefix:
            return f"{self.bucket_prefix}/chat_history/chat_store-{session_id}.json"
        return f"chat_history/chat_store-{session_id}.json"

    def retrieve_chat_history(self, session_id: int) -> List[RagStudioChatMessage]:
        """Retrieve chat history from S3."""
        s3_key = self._get_s3_key(session_id)

        try:
            # Create a temporary file to download the chat history
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
                temp_path = temp_file.name

            # Download the chat history from S3
            self.s3_client.download_file(self.bucket_name, s3_key, temp_path)

            # Load the chat history from the temporary file
            with open(temp_path, "r") as f:
                chat_history_data = json.load(f)

            # Convert the JSON data to RagStudioChatMessage objects
            results: list[RagStudioChatMessage] = []
            for message_data in chat_history_data:
                results.append(RagStudioChatMessage(**message_data))

            return results

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # If the file doesn't exist, return an empty list
                logger.info(f"No chat history found for session {session_id}")
                return []
            else:
                # Re-raise other client errors
                logger.error(
                    f"Error retrieving chat history for session {session_id}: {e}"
                )
                raise
        except Exception as e:
            logger.error(f"Error retrieving chat history for session {session_id}: {e}")
            raise

    def clear_chat_history(self, session_id: int) -> None:
        """Clear chat history for a session."""
        # Create an empty list for chat history
        empty_chat_history = []

        # Create a temporary file to save the empty chat history
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_path = temp_file.name
            json.dump(empty_chat_history, temp_file)

        # Upload the empty chat history to S3
        s3_key = self._get_s3_key(session_id)
        self.s3_client.upload_file(temp_path, self.bucket_name, s3_key)

    def delete_chat_history(self, session_id: int) -> None:
        """Delete chat history for a session."""
        s3_key = self._get_s3_key(session_id)

        try:
            # Delete the chat history from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchKey":
                # Only log and re-raise if it's not a "file not found" error
                logger.error(
                    f"Error deleting chat history for session {session_id}: {e}"
                )
                raise
        except Exception as e:
            logger.error(f"Error deleting chat history for session {session_id}: {e}")
            raise

    def append_to_history(
        self, session_id: int, messages: List[RagStudioChatMessage]
    ) -> None:
        """Append messages to chat history."""
        s3_key = self._get_s3_key(session_id)

        try:
            # Create a temporary file to download the existing chat history
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Try to download the existing chat history from S3
                self.s3_client.download_file(self.bucket_name, s3_key, temp_path)

                # Load the existing chat history
                with open(temp_path, "r") as f:
                    chat_history_data = json.load(f)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    # If the file doesn't exist, create a new empty chat history
                    chat_history_data = []
                else:
                    # Re-raise other client errors
                    raise

            # Append the new messages to the chat history
            for message in messages:
                chat_history_data.append(message.model_dump())

            # Write the updated chat history to the temporary file
            with open(temp_path, "w") as f:
                json.dump(chat_history_data, f)

            # Upload the updated chat history to S3
            self.s3_client.upload_file(temp_path, self.bucket_name, s3_key)

        except Exception as e:
            logger.error(
                f"Error appending to chat history for session {session_id}: {e}"
            )
            raise
