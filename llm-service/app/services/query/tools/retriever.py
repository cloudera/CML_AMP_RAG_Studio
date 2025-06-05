#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
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

from typing import Any

from crewai.tools import BaseTool
from crewai_tools.tools.llamaindex_tool.llamaindex_tool import LlamaIndexTool

from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.schema import TextNode
from llama_index.core.tools import RetrieverTool, ToolOutput, ToolMetadata
from pydantic import BaseModel, Field

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration


class RetrieverToolInput(BaseModel):
    """Input Schema for the RetrieverTool."""

    query: str = Field(
        ...,
        description="The query to search for in the index.",
    )


class RetrieverToolWithNodeInfo(RetrieverTool):
    """
    Retriever tool.

    A tool making use of a retriever.

    Args:
        retriever (BaseRetriever): A retriever.
        metadata (ToolMetadata): The associated metadata of the query engine.
        node_postprocessors (Optional[List[BaseNodePostprocessor]]): A list of
            node postprocessors.
    """

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = ""
        if args is not None:
            query_str += ", ".join([str(arg) for arg in args]) + "\n"
        if kwargs is not None:
            query_str += (
                ", ".join([f"{k!s} is {v!s}" for k, v in kwargs.items()]) + "\n"
            )
        if query_str == "":
            raise ValueError("Cannot call query engine without inputs")

        docs = self._retriever.retrieve(query_str)
        docs = self._apply_node_postprocessors(docs, QueryBundle(query_str))
        content = ""
        for doc in docs:
            node_copy = doc.node.model_copy()
            if isinstance(node_copy, TextNode):
                node_copy.text_template = "{metadata_str}\n{content}"
                node_copy.metadata_template = "{key} = {value}"
                content += (
                    f"node_id = {node_copy.node_id}\n"
                    + f"score = {doc.score}\n"
                    + node_copy.get_content()
                    + "\n\n"
                )
        return ToolOutput(
            content=content,
            tool_name=self.metadata.name if self.metadata.name else "RetrieverTool",
            raw_input={"input": query_str},
            raw_output=docs,
        )

    async def acall(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = ""
        if args is not None:
            query_str += ", ".join([str(arg) for arg in args]) + "\n"
        if kwargs is not None:
            query_str += (
                ", ".join([f"{k!s} is {v!s}" for k, v in kwargs.items()]) + "\n"
            )
        if query_str == "":
            raise ValueError("Cannot call query engine without inputs")
        docs = await self._retriever.aretrieve(query_str)
        content = ""
        docs = self._apply_node_postprocessors(docs, QueryBundle(query_str))
        for doc in docs:
            node_copy = doc.node.model_copy()
            if isinstance(node_copy, TextNode):
                node_copy.text_template = "{metadata_str}\n{content}"
                node_copy.metadata_template = "{key} = {value}"
                content += (
                    f"node_id = {node_copy.node_id}\n"
                    + f"score = {doc.score}\n"
                    + node_copy.get_content()
                    + "\n\n"
                )
        return ToolOutput(
            content=content,
            tool_name=self.metadata.name if self.metadata.name else "RetrieverTool",
            raw_input={"input": query_str},
            raw_output=docs,
        )


def build_retriever_tool(
    retriever: BaseRetriever, summaries: dict[int, str]
) -> BaseTool:
    # fetch summary fromm index if available
    summary_str = "\n".join(summaries.values())
    retriever_tool = RetrieverToolWithNodeInfo(
        retriever=retriever,
        metadata=ToolMetadata(
            name="Retriever",
            description=(
                "A tool to retrieve relevant information from "
                "the index. It takes a query of type string and returns relevant nodes from the index."
                f"The index summaries are: {summary_str}"
                if summary_str
                else "Assume the index has relevant information about the user's question."
            ),
            fn_schema=RetrieverToolInput,
        ),
    )
    crewai_retriever_tool = LlamaIndexTool.from_tool(retriever_tool)
    return crewai_retriever_tool
