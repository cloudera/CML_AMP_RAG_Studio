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
import logging

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.storage import StorageContext
from pydantic import BaseModel

from ..rag_types import RagPredictConfiguration
from . import models, rag_vector_store
from .chat_store import RagContext
from .utils import get_last_segment

logger = logging.getLogger(__name__)


class RagIndexDocumentConfiguration(BaseModel):
    # TODO: Add more params
    chunk_size: int = 512  # this is llama-index's default
    chunk_overlap: int = 10  # percentage of tokens in a chunk (chunk_size)


def download_and_index(
    tmpdirname: str,
    data_source_id: int,
    configuration: RagIndexDocumentConfiguration,
    s3_document_key: str,
) -> None:
    try:
        documents = SimpleDirectoryReader(tmpdirname).load_data()
        document_id = get_last_segment(s3_document_key)
        for document in documents:
            document.id_ = document_id  # this is a terrible way to assign the doc id...
            document.metadata["document_id"] = document_id
    except Exception as e:
        logger.error(
            "error loading document from temporary directory %s",
            tmpdirname,
        )
        raise HTTPException(
            status_code=422,
            detail=f"error loading document from temporary directory {tmpdirname}",
        ) from e

    logger.info("instantiating vector store")
    vector_store = rag_vector_store.create_rag_vector_store(
        data_source_id
    ).access_vector_store()
    logger.info("instantiated vector store")

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    chunk_overlap_tokens = int(
        configuration.chunk_overlap * 0.01 * configuration.chunk_size
    )

    logger.info("indexing document")
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=models.get_embedding_model(),
        show_progress=False,
        transformations=[
            SentenceSplitter(
                chunk_size=configuration.chunk_size,
                chunk_overlap=chunk_overlap_tokens,
            ),
        ],
    )
    logger.info("indexed document")


def check_data_source_exists(data_source_size: int) -> None:
    if data_source_size == -1:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")


def size_of(data_source_id: int) -> int:
    vector_store = rag_vector_store.create_rag_vector_store(data_source_id)
    return vector_store.size()


def chunk_contents(data_source_id: int, chunk_id: str) -> str:
    vector_store = rag_vector_store.create_rag_vector_store(
        data_source_id
    ).access_vector_store()
    node = vector_store.get_nodes([chunk_id])[0]
    return node.get_content()


def delete(data_source_id: int) -> None:
    vector_store = rag_vector_store.create_rag_vector_store(data_source_id)
    vector_store.delete()


def delete_document(data_source_id: int, document_id: str) -> None:
    vector_store = rag_vector_store.create_rag_vector_store(
        data_source_id
    ).access_vector_store()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=models.get_embedding_model(),
    )
    index.delete_ref_doc(document_id)


def query(
    data_source_id: int,
    query_str: str,
    configuration: RagPredictConfiguration,
    chat_history: list[RagContext],
) -> AgentChatResponse:
    vector_store = rag_vector_store.create_rag_vector_store(
        data_source_id
    ).access_vector_store()
    embedding_model = models.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    logger.info("fetched Qdrant index")

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=configuration.top_k,
        embed_model=embedding_model,  # is this needed, really, if it's in the index?
    )
    # TODO: factor out LLM and chat engine into a separate function
    llm = models.get_llm(model_name=configuration.model_name)

    response_synthesizer = get_response_synthesizer(llm=llm)
    query_engine = RetrieverQueryEngine(
        retriever=retriever, response_synthesizer=response_synthesizer
    )
    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        llm=llm,
    )

    logger.info("querying chat engine")
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    try:
        chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.info("query response received from chat engine")
        return chat_response
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error
