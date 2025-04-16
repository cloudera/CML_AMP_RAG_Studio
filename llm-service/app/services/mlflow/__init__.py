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
import os
import re
import uuid
from datetime import datetime
from typing import Any, Optional

import mlflow
from mlflow.entities import Experiment, Run

from app.config import settings
from app.services.chat_store import RagStudioChatMessage, RagPredictSourceNode
from app.services.metadata_apis import data_sources_metadata_api, session_metadata_api
from app.services.metadata_apis.session_metadata_api import Session
from app.services.query.query_configuration import QueryConfiguration

# mypy: disable-error-code="no-untyped-call"


def chat_log_ml_flow_table(message: RagStudioChatMessage) -> dict[str, Any]:
    source_nodes: list[RagPredictSourceNode] = message.source_nodes

    query = message.rag_message.user
    response = message.rag_message.assistant

    flattened_nodes = [node.model_dump() for node in source_nodes]
    return {
        "data": {
            "response_id": message.id,
            "node_id": list(map(lambda x: x.get("node_id"), flattened_nodes)),
            "doc_id": list(map(lambda x: x.get("doc_id"), flattened_nodes)),
            "source_file_name": list(
                map(lambda x: x.get("source_file_name"), flattened_nodes)
            ),
            "score": list(map(lambda x: x.get("score"), flattened_nodes)),
            "query": query,
            "response": response,
            "input_word_count": len(re.findall(r"\w+", query)),
            "output_word_count": len(re.findall(r"\w+", response)),
            "condensed_question": message.condensed_question,
        },
        "artifact_file": "response_details.json",
    }


def chat_log_ml_flow_params(
    session: Session, query_configuration: QueryConfiguration, user_name: Optional[str]
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
        "project_id": session.project_id,
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
    user_name: Optional[str],
) -> None:
    params = chat_log_ml_flow_params(session, query_configuration, user_name)
    source_nodes: list[RagPredictSourceNode] = new_chat_message.source_nodes
    metrics: dict[str, Any] = {
        "source_nodes_count": len(source_nodes),
        "max_score": (source_nodes[0].score if source_nodes else 0.0),
        **{
            evaluation.name: evaluation.value
            for evaluation in new_chat_message.evaluations
        },
    }

    write_mlflow_run_json(
        experiment_name=f"session_{session.id}",
        run_name=f"{response_id}",
        data={
            "params": params,
            "tags": {
                "response_id": response_id,
            },
            "metrics": metrics,
            "table": chat_log_ml_flow_table(new_chat_message),
        },
    )


def record_direct_llm_mlflow_run(
    response_id: str, session: Session, user_name: Optional[str]
) -> None:
    write_mlflow_run_json(
        f"session_{session.id}",
        f"{response_id}",
        {
            "params": {
                "inference_model": session.inference_model,
                "exclude_knowledge_base": True,
                "session_id": session.id,
                "data_source_ids": session.data_source_ids,
                "user_name": user_name,
            },
            "tags": {
                "response_id": response_id,
                "direct_llm": True,
            },
        },
    )


def write_mlflow_run_json(
    experiment_name: str, run_name: str, data: dict[str, Any]
) -> None:
    contents = {
        "experiment_name": experiment_name,
        "run_name": run_name,
        "status": "pending",
        "created_at": datetime.now().timestamp(),
        **data,
    }
    with open(
        f"{settings.mlflow_reconciler_data_path}/{str(uuid.uuid4())}.json",
        "w",
    ) as f:
        json.dump(contents, f)


def rating_mlflow_log_metric(
    rating: bool, response_id: str, session_id: int, user_name: Optional[str]
) -> None:
    session = session_metadata_api.get_session(session_id, user_name=user_name)
    experiment: Experiment = mlflow.set_experiment(
        experiment_name=f"session_{session.name}_{session.id}"
    )
    runs: list[Run] = mlflow.search_runs(
        [experiment.experiment_id],
        filter_string=f"tags.response_id='{response_id}'",
        output_format="list",
    )

    for run in runs:
        value: int = 1 if rating else -1
        mlflow.log_metric("rating", value, run_id=run.info.run_id)


def feedback_mlflow_log_table(feedback: str, response_id: str, session_id: int, user_name: Optional[str]) -> None:
    session = session_metadata_api.get_session(session_id, user_name=user_name)
    experiment: Experiment = mlflow.set_experiment(
        experiment_name=f"session_{session.name}_{session.id}"
    )
    runs: list[Run] = mlflow.search_runs(
        [experiment.experiment_id],
        filter_string=f"tags.response_id='{response_id}'",
        output_format="list",
    )
    for run in runs:
        mlflow.log_table(
            data={"feedback": feedback},
            artifact_file="feedback.json",
            run_id=run.info.run_id,
        )
