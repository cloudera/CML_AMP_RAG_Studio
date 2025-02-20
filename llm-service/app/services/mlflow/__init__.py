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

import re
from pathlib import Path
from typing import Any, Sequence

import mlflow
from mlflow import MlflowClient
from mlflow.entities import Experiment, Param, Metric
from pydantic import BaseModel

from app.services.chat_store import RagStudioChatMessage, RagPredictSourceNode
from app.services.metadata_apis import data_sources_metadata_api
from app.services.metadata_apis.data_sources_metadata_api import RagDataSource
from app.services.metadata_apis.session_metadata_api import Session
from app.services.query.query_configuration import QueryConfiguration


def chat_log_ml_flow_table(message: RagStudioChatMessage) -> None:
    source_nodes: list[RagPredictSourceNode] = message.source_nodes

    query = message.rag_message.user
    response = message.rag_message.assistant

    flattened_nodes = [node.model_dump() for node in source_nodes]
    mlflow.log_table(
        {
            "response_id": message.id,
            "node_id": map(lambda x: x.get("node_id"), flattened_nodes),
            "doc_id": map(lambda x: x.get("doc_id"), flattened_nodes),
            "source_file_name": map(
                lambda x: x.get("source_file_name"), flattened_nodes
            ),
            "score": map(lambda x: x.get("score"), flattened_nodes),
            "query": query,
            "response": response,
            "input_word_count": len(re.findall(r"\w+", query)),
            "output_word_count": len(re.findall(r"\w+", response)),
            "condensed_question": message.condensed_question,
        },
        artifact_file="response_details.json",
    )


def chat_log_ml_flow_params(
    session: Session, query_configuration: QueryConfiguration, user_name: str
) -> dict[str, Any]:
    data_source_metadata = data_sources_metadata_api.get_metadata(
        session.data_source_ids[0]
    )
    return {
        "top_k": query_configuration.top_k,
        "inference_model": query_configuration.model_name,
        "rerank_model_name": query_configuration.rerank_model_name,
        "exclude_knowledge_base": query_configuration.exclude_knowledge_base,
        "use_question_condensing": query_configuration.use_question_condensing,
        "use_hyde": query_configuration.use_hyde,
        "use_summary_filter": query_configuration.use_summary_filter,
        "session_id": session.id,
        "data_source_ids": session.data_source_ids,
        "user_name": user_name,
        "embedding_model": data_source_metadata.embedding_model,
        "chunk_size": data_source_metadata.chunk_size,
        "summarization_model": data_source_metadata.summarization_model,
        "chunk_overlap_percent": data_source_metadata.chunk_overlap_percent,
    }


def record_rag_mlflow_run(
    new_chat_message: RagStudioChatMessage,
    query_configuration: QueryConfiguration,
    response_id: str,
    session: Session,
    user_name: str,
) -> None:
    experiment: Experiment = mlflow.set_experiment(
        experiment_name=f"session_{session.name}_{session.id}"
    )

    # mlflow.set_experiment_tag("session_id", session.id)
    run = mlflow.start_run(
        experiment_id=experiment.experiment_id, run_name=f"{response_id}"
    )
    client = MlflowClient()
    params = chat_log_ml_flow_params(session, query_configuration, user_name)
    source_nodes: list[RagPredictSourceNode] = new_chat_message.source_nodes
    metrics = {
        "source_nodes_count": len(source_nodes),
        "max_score": (source_nodes[0].score if source_nodes else 0.0),
        **{
            evaluation.name: evaluation.value
            for evaluation in new_chat_message.evaluations
        },
    }
    client.log_batch(
        run.info.run_id,
        tags={"response_id": response_id},
        params=params,
        metrics=metrics,
    )
    chat_log_ml_flow_table(new_chat_message)
    mlflow.end_run()


def record_direct_llm_mlflow_run(
    response_id: str, session: Session, user_name: str
) -> None:
    experiment = mlflow.set_experiment(
        experiment_name=f"session_{session.name}_{session.id}"
    )
    run = mlflow.start_run(
        experiment_id=experiment.experiment_id, run_name=f"{response_id}"
    )
    params: Sequence[Param] = [
        Param("inference_model", session.inference_model),
        Param("exclude_knowledge_base", True),
        Param("session_id", session.id),
        Param("data_source_ids", session.data_source_ids),
        Param("user_name", user_name),
    ]
    client = MlflowClient()
    client.log_batch(
        run.info.run_id,
        tags={"response_id": response_id, "direct_llm": True},
        params=params,
    )
    mlflow.end_run()


class RagIndexDocumentConfiguration(BaseModel):
    chunk_size: int = 512  # this is llama-index's default
    chunk_overlap: int = 10  # percentage of tokens in a chunk (chunk_size)


class RagIndexDocumentRequest(BaseModel):
    s3_bucket_name: str
    s3_document_key: str
    original_filename: str
    configuration: RagIndexDocumentConfiguration = RagIndexDocumentConfiguration()


def data_source_record_run(
    datasource: RagDataSource,
    doc_id: str,
    file_path: Path,
    request: RagIndexDocumentRequest,
) -> None:
    experiment: Experiment = mlflow.set_experiment(
        experiment_name=f"datasource_{datasource.name}_{datasource.id}"
    )
    run = mlflow.start_run(
        experiment_id=experiment.experiment_id, run_name=f"doc_{doc_id}"
    )
    #  Todo: Figure out if we care about the timestamp or step but they're required
    metrics = [
        Metric("file_size_bytes", file_path.stat().st_size, timestamp=0, step=0),
    ]
    params: Sequence[Param] = [
        Param("data_source_id", value=str(datasource.id)),
        Param("embedding_model", value=datasource.embedding_model),
        Param("summarization_model", value=datasource.summarization_model),
        Param("chunk_size", value=str(request.configuration.chunk_size)),
        Param("chunk_overlap", value=str(request.configuration.chunk_overlap)),
        Param("file_name", value=request.original_filename),
        Param("file_size_bytes", value=str(file_path.stat().st_size)),
    ]

    client = MlflowClient()
    client.log_batch(run_id=run.info.run_id, metrics=metrics, params=params)
    mlflow.end_run()
