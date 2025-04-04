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
import copy
import functools
import random
import uuid
from typing import Any, TypeVar, Optional

import hypothesis
from hypothesis import given, example
from hypothesis import strategies as st
from mlflow.entities import RunInfo, Run, RunData, Param

from app.services.metrics import MetricFilter, get_relevant_runs


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
            5,
        ),
        project_id=st_filter_value(
            RunMetricsStrategies.project_id(),
            5,
        ),
        inference_model=st_filter_value(
            RunMetricsStrategies.inference_model(),
            "unused_inference_model",
        ),
        rerank_model=st_filter_value(
            RunMetricsStrategies.rerank_model(),
            "unused_rerank_model",
        ),
        has_rerank_model=...,  # TODO: this clashes with rerank_model
        top_k=st_filter_value(
            RunMetricsStrategies.top_k(),
            5,
        ),
        session_id=st_filter_value(
            RunMetricsStrategies.session_id(),
            5,
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
        params=[Param(key=key, value=str(value)) for key, value in kwargs.items() if value is not None],
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
def test_filter_runs(runs: list[Run], metric_filter: MetricFilter) -> None:
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


def create_run_from_filter(metric_filter: MetricFilter, key_to_jostle: Optional[str] = None) -> Run:
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

    if key_to_jostle == 'has_rerank_model':
        if has_rerank_model:
            run_data["rerank_model_name"] = run_data.get("rerank_model_name", "rerank_model_1")
        else:
            run_data["rerank_model_name"] = None


    return make_test_run(**run_data)
