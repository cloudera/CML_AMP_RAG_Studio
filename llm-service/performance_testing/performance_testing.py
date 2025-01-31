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
import itertools
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

test_runtime_config = {
    "reranking_model": [
        model.model_id for model in models.get_available_rerank_models()
    ],
    "synthesis_model": ["meta.llama3-1-8b-instruct-v1:0"],
    "top_k": [5, 10],
    "hyde": [True, False],
}


# usage: uv run --env-file=../.env performance_testing/performance_testing.py <data_source_id> questions_mini.csv
def main():
    file: str = sys.argv[2]
    data_source_id = int(sys.argv[1])
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), file)), "r") as f:
        df = pd.read_csv(f)
        questions: list[str] = df["Question"].tolist()

    with open(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "raw_results.csv")), "a"
    ) as details:
        for config in [
            dict(zip(test_runtime_config.keys(), values))
            for values in itertools.product(*test_runtime_config.values())
        ]:
            print(f"Config: {config}")
            top_k = config["top_k"]
            hyde = config["hyde"]
            reranking_model = config["reranking_model"]
            synthesis_model = config["synthesis_model"]

            metadata = get_metadata(data_source_id)
            summarization_model = metadata.summarization_model
            chunk_size = metadata.chunk_size

            score_sum = 0
            question_count = 0
            max_score = 0
            max_score_sum = 0
            min_max_score = 10000000
            relevance_sum = 0
            faithfulness_sum = 0
            for question in questions:
                chat_engine = setup(
                    data_source_id=data_source_id,
                    hyde=hyde,
                    top_k=top_k,
                    synthesis_model=synthesis_model,
                    reranking_model=reranking_model,
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
                relevance_sum += relevance
                faithfulness_sum += faithfulness

                nodes = chat_response.source_nodes

                if nodes:
                    question_count += 1
                    question_max = max(node.score for node in nodes)
                    max_score = max(max_score, question_max)
                    avg_score = sum(node.score for node in nodes) / len(nodes)
                    score_sum += avg_score
                    max_score_sum += max_score
                    min_max_score = min(max_score, min_max_score)
                    #  timestamp,chunk_size, hyde, summarization_model,reranking_model,top_k, file_name_1, max_score, relevance, faithfulness, question
                    details.write(
                        f'{time.time()},{chunk_size},{hyde},{summarization_model},{reranking_model},{top_k},{nodes[0].metadata.get("file_name")},{question_max},{relevance},{faithfulness},"{question}"\n'
                    )
                details.flush()

            average_average_score = score_sum / question_count
            average_max_score = max_score_sum / question_count
            relevance_average = relevance_sum / question_count
            faithfulness_average = faithfulness_sum / question_count
            print(f"{chat_engine._configuration=}")
            # print(f"Average score: {average_average_score}")
            with open(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "results.csv")),
                "a",
            ) as f:
                # chunk_size,summarization_model,reranking_model,synthesis_model,hyde,top_k,average_max_score,min_max_score,relevance_average,faithfulness_average
                f.write(
                    f"{chunk_size},{summarization_model},{reranking_model},{synthesis_model},{hyde},{top_k},{average_max_score},{min_max_score},{relevance_average},{faithfulness_average}\n"
                )
                f.flush()


def setup(
    data_source_id: int,
    hyde=True,
    top_k: int = 5,
    synthesis_model="meta.llama3-1-8b-instruct-v1:0",
    reranking_model="amazon.rerank-v1:0",
) -> FlexibleContextChatEngine:
    model_name = synthesis_model
    rerank_model = reranking_model
    query_configuration = QueryConfiguration(
        top_k=5,
        model_name=model_name,
        use_question_condensing=True,
        use_hyde=hyde,
        rerank_model_name=rerank_model,
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
