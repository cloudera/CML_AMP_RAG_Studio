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
import random
import json

from hypothesis import strategies as st, given
from mlflow.entities import RunInfo, Run, RunData, Param

from app.services.metrics import MetricFilter, get_relevant_runs


def make_test_run(**kwargs) -> Run:
    return Run(
        run_info=RunInfo(
            run_uuid="",
            experiment_id="",
            user_id="",
            status="RUNNING",
            start_time=1234,
            end_time=5432,
            lifecycle_stage="hello",
        ),
        run_data=RunData(
            params=[
                Param(key=name, value=json.dumps(value))
                for name, value in kwargs.items()
            ],
        ),
    )


@st.composite
def runs(
    draw: st.DrawFn,
    min_runs: int = 0,
    max_runs: int = 100,
    max_data_source_ids: int = 5,
) -> list[Run]:
    if min_runs > max_runs:
        raise ValueError("min_runs must be less than or equal to max_runs")
    if max_data_source_ids > max_runs:
        raise ValueError("max_data_source_ids must be less than or equal to max_runs")

    num_runs: int = draw(st.integers(min_runs, max_runs))
    inference_models = st.sampled_from(["model1", "model2", "model3"])
    data_source_ids: list[int] = draw(
        st.lists(
            st.integers(min_value=1, max_value=6),
            min_size=max(min_runs, 1),
            max_size=max_data_source_ids,
        )
    )

    generated_runs: list[Run] = []
    for data_source_id in data_source_ids:
        generated_runs.append(make_test_run(data_source_ids=[data_source_id], model_name = draw(inference_models)))
    for _ in range(len(data_source_ids), num_runs):
        data_source_id = draw(st.sampled_from(data_source_ids))
        generated_runs.append(make_test_run(data_source_ids=[data_source_id], model_name = draw(inference_models)))
    random.shuffle(generated_runs)
    return generated_runs


@given(
    runs=runs(),
    metric_filter=st.builds(
        MetricFilter,
        data_source_id=st.one_of(
            st.none(),
            st.integers(min_value=1, max_value=6),
        ),
        inference_model=st.sampled_from(["model1", "model2", "model3", None]),
    ),
)
def test_filter_runs(runs: list[Run], metric_filter: MetricFilter):
    print(f"{metric_filter=}")
    results = get_relevant_runs(metric_filter, runs)
    if metric_filter.data_source_id is None:
        assert results == runs
    for run in results:
        if metric_filter.data_source_id is not None:
            assert [metric_filter.data_source_id] == json.loads(
                run.data.params["data_source_ids"]
            )
        else:
            pass  # TODO: Add tests for other filters
