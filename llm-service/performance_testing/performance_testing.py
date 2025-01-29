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
import os
import sys
import time

import pandas as pd
from llama_index.core.chat_engine.types import AgentChatResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.metadata_apis.data_sources_metadata_api import get_metadata
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration

from llama_index.core import VectorStoreIndex

from app.ai.vector_stores.qdrant import QdrantVectorStore
from app.services import models, evaluators
from app.services.query.querier import CUSTOM_PROMPT
from app.services.query.chat_engine import FlexibleContextChatEngine


# usage: uv run --env-file=../.env performance_testing/performance_testing.py <data_source_id> questions_mini.csv
def main():
    data_source_id: int = int(sys.argv[1])
    file: str = sys.argv[2]
    summarization_model = get_metadata(data_source_id).summarization_model
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), file)), "r") as f:
        df = pd.read_csv(f)
        questions: list[str] = df["Question"].tolist()

    with open(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "raw_results.csv")), "a"
    ) as details:
        for hyde in [True, False]:
            for condensing in [False]:
                print(f"Running with hyde={hyde}")
                score_sum = 0
                score_count = 0
                max_score = 0
                for question in questions:
                    top_k = 5
                    chat_engine = setup(
                        use_question_condensing=condensing,
                        use_hyde=hyde,
                        data_source_id=data_source_id,
                        top_k=top_k,
                    )
                    chat_response: AgentChatResponse = chat_engine.chat(
                        message=question, chat_history=None
                    )
                    # Relevance - Measures if the response and source nodes match the query. This is useful for measuring if the query was actually answered by the response.
                    # Faithfulness - Measures if the response from a query engine matches any source nodes. This is useful for measuring if the response was hallucinated.
                    relevance, faithfulness = evaluators.evaluate_response(
                        query=question,
                        chat_response=chat_response,
                        model_name=summarization_model,
                    )

                    nodes = chat_response.source_nodes

                    if nodes:
                        question_max = max(node.score for node in nodes)
                        max_score = max(max_score, question_max)
                        avg_score = sum(node.score for node in nodes) / len(nodes)
                        score_sum += avg_score
                        score_count += 1
                        #  timestamp, hyde, condensing, two_stage, top_k, file_name_1, max_score, relevance, faithfulness, question
                        details.write(
                            f'{time.time()},{hyde},{condensing},{summarization_model is not None},{top_k},{nodes[0].metadata.get("file_name")},{question_max},{relevance},{faithfulness},"{question}"\n'
                        )
                    details.flush()

                average_score = score_sum / score_count
                print(f"{chat_engine._configuration=}")
                print(f"Average score: {average_score}")
                with open(
                    os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "results.csv")
                    ),
                    "a",
                ) as f:
                    f.write(f"{hyde},{max_score},{average_score}\n")
                    f.flush()


def setup(
    data_source_id: int, use_question_condensing=True, use_hyde=True, top_k: int = 5
) -> FlexibleContextChatEngine:

    model_name = "meta.llama3-1-8b-instruct-v1:0"
    rerank_model = "amazon.rerank-v1:0"
    query_configuration = QueryConfiguration(
        top_k=5,
        model_name=model_name,
        use_question_condensing=use_question_condensing,
        use_hyde=use_hyde,
        rerank_model_name=rerank_model
    )
    llm = models.get_llm(model_name=query_configuration.model_name)
    qdrant_store = QdrantVectorStore.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    retriever = FlexibleRetriever(
        configuration=query_configuration,
        index=index,
        embedding_model=embedding_model,  # is this needed, really, if it's in the index?
        data_source_id=data_source_id,
        llm=llm,
    )

    chat_engine = FlexibleContextChatEngine.from_defaults(
        llm=llm,
        condense_question_prompt=CUSTOM_PROMPT,
        retriever=retriever,
        node_postprocessors=[models.get_reranking_model(rerank_model, top_k)],
    )
    chat_engine._configuration = query_configuration
    return chat_engine


if __name__ == "__main__":
    for _ in range(1):
        main()
