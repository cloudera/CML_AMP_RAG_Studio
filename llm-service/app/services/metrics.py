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
import pathlib
from collections import Counter
from typing import Optional

import mlflow
import pandas as pd
from mlflow.entities import Run, FileInfo
from pydantic import BaseModel

STANDARD_FEEDBACK = [
    "Inaccurate",
    "Not Helpful",
    "Out of date",
    "Too short",
    "Too long",
]


class Metrics(BaseModel):
    positive_ratings: int
    negative_ratings: int
    no_ratings: int
    count_of_interactions: int
    count_of_direct_interactions: int
    aggregated_feedback: dict[str, int]
    unique_users: int
    max_score_over_time: list[tuple[int, float]]
    input_word_count_over_time: list[tuple[int, int]]
    output_word_count_over_time: list[tuple[int, int]]


class MetricFilter(BaseModel):
    data_source_id: Optional[int]
    inference_model: Optional[str]


def filter_runs(metric_filter: MetricFilter) -> list[Run]:
    runs: list[Run] = mlflow.search_runs(
        output_format="list", search_all_experiments=True
    )
    return get_relevant_runs(metric_filter, runs)


def get_relevant_runs(metric_filter, runs):
    def filter_by_parameters(r: Run) -> bool:
        if metric_filter.data_source_id:
            return metric_filter.data_source_id in json.loads(
                r.data.params.get("data_source_ids", "[]")
            )
        else:
            return True

    return list(
        filter(
            filter_by_parameters,
            runs,
        )
    )


def generate_metrics(metric_filter: MetricFilter) -> Metrics:
    relevant_runs = filter_runs(metric_filter)
    positive_ratings = len(
        list(filter(lambda r: r.data.metrics.get("rating", 0) > 0, relevant_runs))
    )
    negative_ratings = len(
        list(filter(lambda r: r.data.metrics.get("rating", 0) < 0, relevant_runs))
    )
    no_ratings = len(
        list(filter(lambda r: r.data.metrics.get("rating", 0) == 0, relevant_runs))
    )
    run: Run
    scores: list[float] = list()
    feedback_entries: list[str] = list()
    unique_users = len(
        set(map(lambda r: r.data.params.get("user_name", "unknown"), relevant_runs))
    )
    count_of_direct_interactions = 0
    max_score_over_time: list[tuple[int, float]] = []
    input_word_count_over_time: list[tuple[int, int]] = []
    output_word_count_over_time: list[tuple[int, int]] = []
    for run in relevant_runs:
        base_artifact_uri: str = run.info.artifact_uri
        artifacts: list[FileInfo] = mlflow.artifacts.list_artifacts(base_artifact_uri)
        if run.data.tags.get("direct_llm") == "True":
            count_of_direct_interactions += 1

        artifact: FileInfo
        for artifact in artifacts:
            ## get the last segment of the path
            name = pathlib.Path(artifact.path).name
            if name == "response_details.json":
                df = load_dataframe_from_artifact(base_artifact_uri, name)
                if "score" in df.columns:
                    scores.extend(df["score"].to_list())
            if name == "feedback.json":
                df = load_dataframe_from_artifact(base_artifact_uri, name)
                if "feedback" in df.columns:
                    feedback_entries.extend(df["feedback"].to_list())
            max_score_over_time.append(
                (run.info.start_time, run.data.metrics.get("max_score", 0))
            )
            input_word_count_over_time.append(
                (run.info.start_time, run.data.metrics.get("input_word_count", 0))
            )
            output_word_count_over_time.append(
                (run.info.start_time, run.data.metrics.get("output_word_count", 0))
            )
    cleaned_feedback = list(
        map(
            lambda feedback: feedback if feedback in STANDARD_FEEDBACK else "Other",
            feedback_entries,
        )
    )
    return Metrics(
        positive_ratings=positive_ratings,
        negative_ratings=negative_ratings,
        no_ratings=no_ratings,
        count_of_interactions=len(relevant_runs),
        count_of_direct_interactions=count_of_direct_interactions,
        aggregated_feedback=(dict(Counter(cleaned_feedback))),
        unique_users=unique_users,
        max_score_over_time=max_score_over_time,
        input_word_count_over_time=input_word_count_over_time,
        output_word_count_over_time=output_word_count_over_time,
    )


def load_dataframe_from_artifact(uri: str, name: str) -> pd.DataFrame:
    artifact_loc = uri + "/" + name
    data = mlflow.artifacts.load_text(artifact_loc)
    return pd.read_json(data, orient="split")
