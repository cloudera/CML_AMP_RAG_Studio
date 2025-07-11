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
import functools
import json
import random
import uuid
from typing import Any, TypeVar, Optional
from unittest.mock import Mock, patch

import hypothesis
import pandas as pd
import pytest
from hypothesis import given, example, settings
from hypothesis import strategies as st
from mlflow.entities import (
    RunInfo,
    Run,
    RunData,
    Param,
    Metric,
    Experiment,
    FileInfo,
    RunTag,
)

from app.services.metrics import (
    MetricFilter,
    get_relevant_runs,
    generate_metrics,
    Metrics,
)
from app.services.metadata_apis.app_metrics_api import MetadataMetrics


# mypy: disable-error-code="no-untyped-call"


class RunMetricsStrategies:
    @staticmethod
    def data_source_id() -> st.SearchStrategy[int]:
        return st.integers(min_value=1, max_value=3)

    @staticmethod
    def project_id() -> st.SearchStrategy[int]:
        return st.integers(min_value=6, max_value=13)

    @staticmethod
    def inference_model() -> st.SearchStrategy[str]:
        return st.sampled_from(
            ["inference_model_1", "inference_model_2", "inference_model_3"]
        )

    @staticmethod
    def rerank_model() -> st.SearchStrategy[str | None]:
        return st.one_of(
            st.none(),
            st.sampled_from(["rerank_model_1", "rerank_model_2", "rerank_model_3"]),
        )

    @staticmethod
    def top_k() -> st.SearchStrategy[int]:
        return st.integers(min_value=1, max_value=3)

    @staticmethod
    def session_id() -> st.SearchStrategy[int]:
        return st.integers(min_value=1, max_value=3)

    @staticmethod
    def use_summary_filter() -> st.SearchStrategy[bool]:
        return st.booleans()

    @staticmethod
    def use_hyde() -> st.SearchStrategy[bool]:
        return st.booleans()

    @staticmethod
    def use_question_condensing() -> st.SearchStrategy[bool]:
        return st.booleans()

    @staticmethod
    def exclude_knowledge_base() -> st.SearchStrategy[bool]:
        return st.booleans()


T = TypeVar("T")


def st_filter_value(
    strategy: st.SearchStrategy[T],
    additional_value: Optional[T] = None,
) -> st.SearchStrategy[T | None]:
    """
    Returns either ``None``, a value from `strategy`, or `additional_value`.

    The idea is that if `strategy` returns possible values for ``Run``s, then this strategy returns values for
    ``MetricFilter``:

    * ``None``, expecting that the filter should not be applied.
    * A value from `strategy`, expecting that the filter should find ``Run``s with that value.
    * `additional_value`, expecting that the filter should not find any ``Run``s.

    """
    strategies: list[st.SearchStrategy[T | None]] = [st.none()]
    if additional_value is not None:
        # additional_value goes second rather than last
        # so that Hypothesis shrinks towards it when searching for failure cases
        strategies.append(st.just(additional_value))
    strategies.append(strategy)

    return st.one_of(*strategies)


def st_metric_filter() -> st.SearchStrategy[MetricFilter]:
    return st.builds(
        MetricFilter,
        data_source_id=st_filter_value(
            RunMetricsStrategies.data_source_id(),
            99,
        ),
        project_id=st_filter_value(
            RunMetricsStrategies.project_id(),
            99,
        ),
        inference_model=st_filter_value(
            RunMetricsStrategies.inference_model(),
            "inference_model_99",
        ),
        rerank_model=st_filter_value(
            RunMetricsStrategies.rerank_model(),
            "rerank_model_99",
        ),
        has_rerank_model=...,  # TODO: this clashes with rerank_model
        top_k=st_filter_value(
            RunMetricsStrategies.top_k(),
            99,
        ),
        session_id=st_filter_value(
            RunMetricsStrategies.session_id(),
            99,
        ),
        use_summary_filter=st_filter_value(
            RunMetricsStrategies.use_summary_filter(),
        ),
        use_hyde=st_filter_value(
            RunMetricsStrategies.use_hyde(),
        ),
        use_question_condensing=st_filter_value(
            RunMetricsStrategies.use_question_condensing(),
        ),
        exclude_knowledge_base=st_filter_value(
            RunMetricsStrategies.exclude_knowledge_base(),
        ),
    )


def make_test_run(**kwargs: Any) -> Run:
    run_info: RunInfo = RunInfo(
        run_uuid=str(uuid.uuid4()),
        experiment_id="",
        user_id="",
        status="RUNNING",
        start_time=1234,
        end_time=5432,
        lifecycle_stage="hello",
    )
    run_data: RunData = RunData(
        params=[
            Param(key=key, value=str(value))
            for key, value in kwargs.items()
            if value is not None
        ],
    )
    return Run(run_info=run_info, run_data=run_data)


@st.composite
def st_runs(
    draw: st.DrawFn,
    min_runs: int = 0,
    max_runs: int = 500,
) -> list[Run]:
    if min_runs > max_runs:
        raise ValueError("min_runs must be less than or equal to max_runs")

    data_source_ids: list[int] = draw(
        st.lists(
            RunMetricsStrategies.data_source_id(),
            min_size=min_runs,
            max_size=max_runs,
        )
    )
    really_make_test_run = functools.partial(
        make_test_run,
        top_k=draw(RunMetricsStrategies.top_k()),
        session_id=draw(RunMetricsStrategies.session_id()),
        use_summary_filter=draw(RunMetricsStrategies.use_summary_filter()),
        use_hyde=draw(RunMetricsStrategies.use_hyde()),
        use_question_condensing=draw(RunMetricsStrategies.use_question_condensing()),
        exclude_knowledge_base=draw(RunMetricsStrategies.exclude_knowledge_base()),
        project_id=draw(RunMetricsStrategies.project_id()),
    )

    generated_runs: list[Run] = []
    for data_source_id in data_source_ids:
        generated_runs.append(
            really_make_test_run(
                data_source_ids=[data_source_id],
                inference_model=draw(RunMetricsStrategies.inference_model()),
                rerank_model_name=draw(RunMetricsStrategies.rerank_model()),
            )
        )
    random.shuffle(generated_runs)
    return generated_runs


@given(
    runs=st_runs(),
    metric_filter=st_metric_filter(),
)
@example(
    runs=[make_test_run(data_source_ids=[5], top_k=i) for i in [1, 2, 3]],
    metric_filter=MetricFilter(top_k=1),
)
@example(
    runs=[make_test_run(data_source_ids=[i]) for i in [1, 2, 3]],
    metric_filter=MetricFilter(data_source_id=1),
)
@settings(max_examples=1000)
def test_filtered_runs(runs: list[Run], metric_filter: MetricFilter) -> None:
    relevant_runs = get_relevant_runs(metric_filter, runs)
    if all(filter_value is None for _, filter_value in metric_filter):
        assert relevant_runs == runs
        return

    # make sure there are no false positives
    for run in relevant_runs:
        for key, filter_value in metric_filter:
            if filter_value is None:
                continue
            if key == "has_rerank_model":
                if filter_value is True:
                    assert run.data.params.get("rerank_model_name") is not None
                else:
                    assert run.data.params.get("rerank_model_name") is None
            elif key == "data_source_id":
                assert run.data.params["data_source_ids"] == str([filter_value])
            elif key == "rerank_model":
                assert run.data.params["rerank_model_name"] == str(filter_value)
            else:
                assert run.data.params[key] == str(filter_value)


@given(metric_filter=st_metric_filter())
@settings(max_examples=1000)
def test_conrado_idea(metric_filter: MetricFilter) -> None:
    hypothesis.assume(metric_filter.data_source_id is not None)
    if not metric_filter.has_rerank_model:
        hypothesis.assume(metric_filter.rerank_model is None)

    run = create_run_from_filter(metric_filter)
    assert get_relevant_runs(metric_filter, [run]) == [run]

    for key, value in metric_filter.model_dump().items():
        if value is None:
            continue
        bad_run = create_run_from_filter(metric_filter, key)
        assert get_relevant_runs(metric_filter, [bad_run]) == []


def create_run_from_filter(
    metric_filter: MetricFilter, key_to_jostle: Optional[str] = None
) -> Run:
    """Create a Run that passes `metric_filter`, or one that fails if `key_to_jostle` is set."""
    # TODO: raise exception if key_to_jostle is not in metric_filter?
    run_data: dict[str, Any] = metric_filter.model_dump()

    if key_to_jostle is not None and key_to_jostle in run_data:
        if isinstance(run_data[key_to_jostle], bool):
            run_data[key_to_jostle] = not run_data[key_to_jostle]
        else:
            run_data[key_to_jostle] *= 2

    run_data["data_source_ids"] = [run_data.pop("data_source_id")]
    run_data["rerank_model_name"] = run_data.pop("rerank_model")

    has_rerank_model = run_data.pop("has_rerank_model")
    if has_rerank_model and run_data["rerank_model_name"] is None:
        run_data["rerank_model_name"] = "rerank_model_1"

    if key_to_jostle == "has_rerank_model" and not has_rerank_model:
        run_data["rerank_model_name"] = None

    return make_test_run(**run_data)


# Tests for generate_metrics function


def create_test_run_with_metrics(
    run_id: str = "test_run_1",
    experiment_id: str = "exp_1",
    start_time: int = 1000,
    rating: float = 1.0,
    max_score: float = 0.8,
    input_word_count: int = 50,
    output_word_count: int = 100,
    faithfulness: float = 0.9,
    relevance: float = 0.85,
    user_name: str = "test_user",
    data_source_ids: list[int] = [1],
    project_id: int = 1,
    inference_model: str = "test_model",
    rerank_model_name: Optional[str] = None,
    direct_llm: bool = False,
    **kwargs: Any,
) -> Run:
    """Create a test run with metrics and parameters for testing generate_metrics."""
    run_info = RunInfo(
        run_uuid=run_id,
        experiment_id=experiment_id,
        user_id="test_user",
        status="FINISHED",
        start_time=start_time,
        end_time=start_time + 1000,
        lifecycle_stage="active",
        artifact_uri=f"artifacts://{run_id}",
    )

    # Create parameters
    params = [
        Param(key="user_name", value=user_name),
        Param(key="data_source_ids", value=json.dumps(data_source_ids)),
        Param(key="project_id", value=str(project_id)),
        Param(key="inference_model", value=inference_model),
    ]

    if rerank_model_name is not None:
        params.append(Param(key="rerank_model_name", value=rerank_model_name))

    # Add any additional parameters from kwargs
    for key, value in kwargs.items():
        params.append(Param(key=key, value=str(value)))

    # Create metrics
    metrics = [
        Metric(key="rating", value=rating, timestamp=start_time, step=0),
        Metric(key="max_score", value=max_score, timestamp=start_time, step=0),
        Metric(
            key="input_word_count", value=input_word_count, timestamp=start_time, step=0
        ),
        Metric(
            key="output_word_count",
            value=output_word_count,
            timestamp=start_time,
            step=0,
        ),
        Metric(key="faithfulness", value=faithfulness, timestamp=start_time, step=0),
        Metric(key="relevance", value=relevance, timestamp=start_time, step=0),
    ]

    # Create tags
    tags = []
    if direct_llm:
        tags.append(RunTag(key="direct_llm", value="True"))

    run_data = RunData(
        params=params,
        metrics=metrics,
        tags=tags,
    )

    return Run(run_info=run_info, run_data=run_data)


@pytest.fixture
def mock_metadata_metrics() -> MetadataMetrics:
    """Mock metadata metrics."""
    return MetadataMetrics(
        number_of_data_sources=5,
        number_of_documents=100,
        number_of_sessions=50,
    )


@pytest.fixture
def sample_experiments() -> list[Experiment]:
    """Sample experiments for testing."""
    return [
        Experiment(
            experiment_id="exp_1",
            name="test_experiment",
            artifact_location="artifacts://exp_1",
            lifecycle_stage="active",
            tags={},
        ),
        Experiment(
            experiment_id="datasource_exp_1",
            name="datasource_test",
            artifact_location="artifacts://datasource_exp_1",
            lifecycle_stage="active",
            tags={},
        ),
    ]


class TestGenerateMetrics:
    """Test suite for the generate_metrics function."""

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    @patch("app.services.metrics.mlflow.artifacts.load_text")
    def test_generate_metrics_basic(
        self,
        mock_load_text: Mock,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test basic metrics generation with simple data."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Create test runs
        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                rating=1.0,
                user_name="user1",
                start_time=1000,
            ),
            create_test_run_with_metrics(
                run_id="run_2",
                rating=-1.0,
                user_name="user2",
                start_time=2000,
            ),
            create_test_run_with_metrics(
                run_id="run_3",
                rating=0.0,
                user_name="user1",
                start_time=3000,
            ),
        ]

        mock_search_runs.return_value = runs
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # Assertions
        assert isinstance(result, Metrics)
        assert result.positive_ratings == 1
        assert result.negative_ratings == 1
        assert result.no_ratings == 1
        assert result.count_of_interactions == 3
        assert result.count_of_direct_interactions == 0
        assert result.unique_users == 2
        assert result.metadata_metrics == mock_metadata_metrics
        assert len(result.max_score_over_time) == 3
        assert len(result.input_word_count_over_time) == 3
        assert len(result.output_word_count_over_time) == 3

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_with_filter(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test metrics generation with filter applied."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Create test runs with different data source IDs
        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                data_source_ids=[1],
                rating=1.0,
            ),
            create_test_run_with_metrics(
                run_id="run_2",
                data_source_ids=[2],
                rating=1.0,
            ),
        ]

        mock_search_runs.return_value = runs
        mock_list_artifacts.return_value = []

        # Execute with filter
        metric_filter = MetricFilter(data_source_id=1)
        result = generate_metrics(metric_filter)

        # Should only count runs with data_source_id=1
        assert result.positive_ratings == 1
        assert result.count_of_interactions == 1

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_with_direct_llm(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test metrics generation with direct LLM interactions."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Create runs with direct LLM tag
        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                direct_llm=True,
                rating=1.0,
            ),
            create_test_run_with_metrics(
                run_id="run_2",
                direct_llm=False,
                rating=1.0,
            ),
        ]

        mock_search_runs.return_value = runs
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # Assertions
        assert result.count_of_interactions == 2
        assert result.count_of_direct_interactions == 1

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    @patch("app.services.metrics.mlflow.artifacts.load_text")
    def test_generate_metrics_with_artifacts(
        self,
        mock_load_text: Mock,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test metrics generation with artifact processing."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                rating=1.0,
            ),
        ]

        mock_search_runs.return_value = runs

        # Mock artifacts
        mock_list_artifacts.return_value = [
            FileInfo(path="response_details.json", is_dir=False, file_size=100),
            FileInfo(path="feedback.json", is_dir=False, file_size=50),
        ]

        # Mock artifact content
        response_details_df = pd.DataFrame(
            {
                "score": [0.8, 0.9, 0.7],
                "other_col": ["a", "b", "c"],
            }
        )
        feedback_df = pd.DataFrame(
            {
                "feedback": ["Inaccurate", "Too short", "Custom feedback"],
                "other_col": ["x", "y", "z"],
            }
        )

        def mock_load_text_side_effect(path: str) -> str:
            if "response_details.json" in path:
                return response_details_df.to_json(orient="split") or "{}"
            elif "feedback.json" in path:
                return feedback_df.to_json(orient="split") or "{}"
            return "{}"

        mock_load_text.side_effect = mock_load_text_side_effect

        # Execute
        result = generate_metrics()

        # Assertions
        assert result.aggregated_feedback == {
            "Inaccurate": 1,
            "Too short": 1,
            "Other": 1,  # Custom feedback should be categorized as "Other"
        }

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_evaluation_averages(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test evaluation averages calculation."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Create runs with faithfulness and relevance metrics
        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                faithfulness=0.8,
                relevance=0.7,
                direct_llm=False,
            ),
            create_test_run_with_metrics(
                run_id="run_2",
                faithfulness=0.9,
                relevance=0.8,
                direct_llm=False,
            ),
            create_test_run_with_metrics(
                run_id="run_3",
                faithfulness=0.6,
                relevance=0.9,
                direct_llm=True,  # This should be excluded from averages
            ),
        ]

        mock_search_runs.return_value = runs
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # FIXED: Now correctly calculates averages by only summing non-direct LLM runs
        # Direct LLM runs (run_3) are excluded from evaluation averages calculation
        # Only non-direct LLM runs are included: (0.8 + 0.9) / 2 = 0.85, (0.7 + 0.8) / 2 = 0.75
        expected_faithfulness = (0.8 + 0.9) / 2  # 0.85
        expected_relevance = (0.7 + 0.8) / 2  # 0.75

        assert result.evaluation_averages["faithfulness"] == expected_faithfulness
        assert result.evaluation_averages["relevance"] == expected_relevance

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_evaluation_averages_only_direct_llm(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test evaluation averages when there are only direct LLM runs."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Create runs with only direct LLM runs (should be excluded from evaluation averages)
        runs = [
            create_test_run_with_metrics(
                run_id="run_1",
                faithfulness=0.8,
                relevance=0.7,
                direct_llm=True,
            ),
            create_test_run_with_metrics(
                run_id="run_2",
                faithfulness=0.9,
                relevance=0.8,
                direct_llm=True,
            ),
        ]

        mock_search_runs.return_value = runs
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # With only direct LLM runs, evaluation averages should be 0
        assert result.evaluation_averages["faithfulness"] == 0
        assert result.evaluation_averages["relevance"] == 0
        assert result.count_of_interactions == 2
        assert result.count_of_direct_interactions == 2

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_empty_runs(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test metrics generation with no runs."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments
        mock_search_runs.return_value = []
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # All counts should be zero
        assert result.positive_ratings == 0
        assert result.negative_ratings == 0
        assert result.no_ratings == 0
        assert result.count_of_interactions == 0
        assert result.count_of_direct_interactions == 0
        assert result.unique_users == 0
        assert result.aggregated_feedback == {}
        assert result.max_score_over_time == []
        assert result.input_word_count_over_time == []
        assert result.output_word_count_over_time == []
        assert result.evaluation_averages["faithfulness"] == 0
        assert result.evaluation_averages["relevance"] == 0

    @patch("app.services.metrics.app_metrics_api.get_metadata_metrics")
    @patch("app.services.metrics.mlflow.search_experiments")
    @patch("app.services.metrics.mlflow.search_runs")
    @patch("app.services.metrics.mlflow.artifacts.list_artifacts")
    def test_generate_metrics_filters_datasource_experiments(
        self,
        mock_list_artifacts: Mock,
        mock_search_runs: Mock,
        mock_search_experiments: Mock,
        mock_get_metadata_metrics: Mock,
        sample_experiments: list[Experiment],
        mock_metadata_metrics: MetadataMetrics,
    ) -> None:
        """Test that datasource experiments are filtered out."""
        # Setup mocks
        mock_get_metadata_metrics.return_value = mock_metadata_metrics
        mock_search_experiments.return_value = sample_experiments

        # Mock search_runs to return different runs for different experiments
        def mock_search_runs_side_effect(
            experiment_ids: list[str], **kwargs: Any
        ) -> list[Run]:
            if experiment_ids == ["exp_1"]:
                return [create_test_run_with_metrics(run_id="run_1")]
            elif experiment_ids == ["datasource_exp_1"]:
                return [create_test_run_with_metrics(run_id="datasource_run_1")]
            return []

        mock_search_runs.side_effect = mock_search_runs_side_effect
        mock_list_artifacts.return_value = []

        # Execute
        result = generate_metrics()

        # Should only process runs from non-datasource experiments
        assert result.count_of_interactions == 1

    def test_generate_metrics_with_none_filter(self) -> None:
        """Test that passing None as filter works correctly."""
        with patch(
            "app.services.metrics.app_metrics_api.get_metadata_metrics"
        ) as mock_get_metadata_metrics:
            with patch("app.services.metrics.filter_runs") as mock_filter_runs:
                mock_get_metadata_metrics.return_value = MetadataMetrics(
                    number_of_data_sources=0,
                    number_of_documents=0,
                    number_of_sessions=0,
                )
                mock_filter_runs.return_value = []

                result = generate_metrics(None)

                # Should create a default MetricFilter and process normally
                assert isinstance(result, Metrics)
                mock_filter_runs.assert_called_once()
                # Verify that a MetricFilter was created (not None)
                args, kwargs = mock_filter_runs.call_args
                assert isinstance(args[0], MetricFilter)
