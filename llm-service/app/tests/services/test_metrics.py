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
import random

from hypothesis import strategies as st, given
from mlflow.entities import RunInfo, Run, RunData, Param

from app.services.metrics import MetricFilter, get_relevant_runs


def make_test_run(**kwargs) -> Run:
    inference_model = kwargs.pop("inference_model")
    data_source_ids = json.dumps(kwargs.pop("data_source_ids"))
    rerank_model = kwargs.pop("rerank_model")
    top_k = kwargs.pop("top_k")
    session_id = kwargs.pop("session_id")
    use_summary_filter = kwargs.pop("use_summary_filter")
    use_hyde = kwargs.pop("use_hyde")
    use_question_condensing = kwargs.pop("use_question_condensing")
    exclude_knowledge_base = kwargs.pop("exclude_knowledge_base")

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
                Param(key="inference_model", value=inference_model),
                Param(key="data_source_ids", value=data_source_ids),
                Param(key="rerank_model_name", value=rerank_model),
                Param(key="top_k", value=str(top_k)),
                Param(key="session_id", value=str(session_id)),
                Param(key="use_summary_filter", value=str(use_summary_filter)),
                Param(key="use_hyde", value=str(use_hyde)),
                Param(
                    key="use_question_condensing", value=str(use_question_condensing)
                ),
                Param(key="exclude_knowledge_base", value=str(exclude_knowledge_base)),
            ],
        ),
    )


@st.composite
def make_runs(
    draw: st.DrawFn,
    min_runs: int = 0,
    max_runs: int = 500,
    max_data_source_ids: int = 5,
) -> list[Run]:
    if min_runs > max_runs:
        raise ValueError("min_runs must be less than or equal to max_runs")
    if max_data_source_ids > max_runs:
        raise ValueError("max_data_source_ids must be less than or equal to max_runs")

    num_runs: int = draw(st.integers(min_runs, max_runs))
    inference_models = st.sampled_from(["model1", "model2", "model3"])
    reranking_models = st.one_of(st.none(), st.sampled_from(
        ["rerank_model1", "rerank_model2", "rerank_model3"]
    ))
    data_source_ids: list[int] = draw(
        st.lists(
            st.integers(min_value=1, max_value=6),
            min_size=max(min_runs, 1),
            max_size=max_data_source_ids,
        )
    )
    top_k: int = draw(st.integers(min_value=1, max_value=20))
    session_id: int = draw(st.integers(min_value=1, max_value=20))
    use_summary_filter: bool = draw(st.booleans())
    use_hyde: bool = draw(st.booleans())
    use_question_condensing: bool = draw(st.booleans())
    exclude_knowledge_base: bool = draw(st.booleans())

    generated_runs: list[Run] = []
    for data_source_id in data_source_ids:
        generated_runs.append(
            make_test_run(
                data_source_ids=[data_source_id],
                inference_model=draw(inference_models),
                rerank_model=draw(reranking_models),
                top_k=top_k,
                session_id=session_id,
                use_summary_filter=use_summary_filter,
                use_hyde=use_hyde,
                use_question_condensing=use_question_condensing,
                exclude_knowledge_base=exclude_knowledge_base,
            )
        )
    for _ in range(len(data_source_ids), num_runs):
        data_source_id = draw(st.sampled_from(data_source_ids))
        generated_runs.append(
            make_test_run(
                data_source_ids=[data_source_id],
                inference_model=draw(inference_models),
                rerank_model=draw(reranking_models),
                top_k=top_k,
                session_id=session_id,
                use_summary_filter=use_summary_filter,
                use_hyde=use_hyde,
                use_question_condensing=use_question_condensing,
                exclude_knowledge_base=exclude_knowledge_base,
            )
        )
    random.shuffle(generated_runs)
    return generated_runs


@given(
    runs=make_runs(),
    metric_filter=st.builds(
        MetricFilter,
        data_source_id=st.one_of(
            st.none(),
            st.integers(min_value=1, max_value=6),
        ),
        inference_model=st.one_of(st.none(), st.sampled_from(["model1", "model2", "model3"])),
        rerank_model=st.one_of(st.none(), st.sampled_from(
            ["rerank_model1", "rerank_model2", "rerank_model3"]
        )),
        top_k=st.one_of(st.none(), st.integers(min_value=1, max_value=20)),
        session_id=st.one_of(st.none(), st.integers(min_value=1, max_value=20)),
        use_summary_filter=st.one_of(st.none(), st.booleans()),
        use_hyde=st.one_of(st.none(), st.booleans()),
        use_question_condensing=st.one_of(st.none(), st.booleans()),
        exclude_knowledge_base=st.one_of(st.none(), st.booleans()),
    ),
)
def test_filter_runs(runs: list[Run], metric_filter: MetricFilter):
    results = get_relevant_runs(metric_filter, runs)
    if all(filtered is None for filtered in metric_filter):
        assert results == runs
        return
    for run in results:
        if metric_filter.data_source_id is not None:
            assert [metric_filter.data_source_id] == json.loads(
                run.data.params["data_source_ids"]
            )
        if metric_filter.inference_model is not None:
            assert run.data.params["inference_model"] == metric_filter.inference_model
        if metric_filter.rerank_model is not None:
            assert run.data.params["rerank_model_name"] == metric_filter.rerank_model
        if metric_filter.top_k is not None:
            assert run.data.metrics["top_k"] == metric_filter.top_k
        if metric_filter.session_id is not None:
            assert run.data.params["session_id"] == metric_filter.session_id
        if metric_filter.use_summary_filter is not None:
            assert run.data.params["use_summary_filter"] == str(
                metric_filter.use_summary_filter
            )
        if metric_filter.use_hyde is not None:
            assert run.data.params["use_hyde"] == str(metric_filter.use_hyde)
        if metric_filter.use_question_condensing is not None:
            assert run.data.params["use_question_condensing"] == str(
                metric_filter.use_question_condensing
            )
        if metric_filter.exclude_knowledge_base is not None:
            assert run.data.params["exclude_knowledge_base"] == str(
                metric_filter.exclude_knowledge_base
            )
