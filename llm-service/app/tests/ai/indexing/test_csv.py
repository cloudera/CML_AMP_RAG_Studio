import time
start_time = time.time()
import tempfile
import uuid
from pathlib import Path

from app.ai.indexing.embedding_indexer import EmbeddingIndexer
from app.ai.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import VectorStoreQuery

from ....services import models


def test_csv_indexing() -> None:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    # Create a simple csv file with 3 rows
    with open(temp_file.name, "w") as f:
        f.write("name,age\nJohn,25\nJane,30\nJim,35")

    data_source_id = 1
    document_id = str(uuid.uuid4())

    vector_store = QdrantVectorStore.for_chunks(data_source_id)

    indexer = EmbeddingIndexer(
        data_source_id,
        splitter=SentenceSplitter(
            chunk_size=100,
            chunk_overlap=0,
        ),
        embedding_model=models.Embedding.get("dummy_model"),
        chunks_vector_store=vector_store,
        llm=None,
    )
    indexer.index_file(Path(temp_file.name), document_id)

    vectors = vector_store.llama_vector_store().query(
        VectorStoreQuery(query_embedding=[0.66] * 1024, similarity_top_k=3)
    )
    assert len(vectors.nodes or []) == 3

    vector_store.delete_document(document_id)

    vectors = vector_store.llama_vector_store().query(
        VectorStoreQuery(query_embedding=[0.66] * 1024, similarity_top_k=3)
    )
    assert len(vectors.nodes or []) == 0

print('tests/ai/indexing/test_csv.py took {time.time() - start_time} seconds to import')
