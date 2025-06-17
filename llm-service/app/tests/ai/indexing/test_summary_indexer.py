import random

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.models import LLM, Embedding


def test_small_input() -> None:
    """Test that when input has 1000 or fewer nodes, it returns the original list."""
    # Create a SummaryIndexer instance with minimal required parameters
    indexer = SummaryIndexer(
        data_source_id=1,
        splitter=SentenceSplitter(),
        llm=LLM.get_noop(),
        embedding_model=Embedding.get_noop(),
    )

    # Create a list of 500 nodes
    nodes = [TextNode(text=f"Node {i}") for i in range(500)]

    # Sample the nodes
    sampled_nodes = indexer.sample_nodes(nodes)

    # Verify that the original list is returned
    assert sampled_nodes == nodes
    assert len(sampled_nodes) == 500


def test_exact_threshold() -> None:
    """Test that when input has exactly 1000 nodes, it returns the original list."""
    indexer = SummaryIndexer(
        data_source_id=1,
        splitter=SentenceSplitter(),
        llm=LLM.get_noop(),
        embedding_model=Embedding.get_noop(),
    )

    # Create a list of 1000 nodes
    nodes = [TextNode(text=f"Node {i}") for i in range(1000)]

    # Sample the nodes
    sampled_nodes = indexer.sample_nodes(nodes)

    # Verify that the original list is returned
    assert sampled_nodes == nodes
    assert len(sampled_nodes) == 1000


def test_large_input() -> None:
    """Test that when input has more than 1000 nodes, it samples correctly."""
    # Set random seed for reproducibility
    random.seed(42)

    indexer = SummaryIndexer(
        data_source_id=1,
        splitter=SentenceSplitter(),
        llm=LLM.get_noop(),
        embedding_model=Embedding.get_noop(),
    )

    # Create a list of 2000 nodes
    nodes = [TextNode(text=f"Node {i}") for i in range(2000)]

    # Sample the nodes
    sampled_nodes = indexer.sample_nodes(nodes)

    # Verify that we get at most 1000 nodes
    assert len(sampled_nodes) == 1000

    # Verify that we get contiguous blocks
    # This is hard to test directly since the blocks are randomly selected
    # But we can check that the sampled nodes are a subset of the original nodes
    for node in sampled_nodes:
        assert node in nodes


def test_contiguous_blocks() -> None:
    """Test that the sampled nodes are in contiguous blocks of 20."""
    # Set random seed for reproducibility
    random.seed(42)

    indexer = SummaryIndexer(
        data_source_id=1,
        splitter=SentenceSplitter(),
        llm=LLM.get_noop(),
        embedding_model=Embedding.get_noop(),
    )

    # Create a list of 2000 nodes with unique identifiable text
    nodes = [TextNode(text=f"Node {i}") for i in range(2000)]

    # Sample the nodes
    sampled_nodes = indexer.sample_nodes(nodes)

    # Find the indices of the sampled nodes in the original list
    indices = [i for i, node in enumerate(nodes) if node in sampled_nodes]

    # Sort the indices
    indices.sort()

    # Check that we have contiguous blocks of 20
    # We should have gaps between blocks, but within each block,
    # indices should be consecutive
    # Note: Two blocks might be contiguous (e.g., one block ends at index 19 and the next starts at index 20)
    # This is valid, but we need to ensure each block has at most 20 nodes
    blocks = []
    current_block = [indices[0]]

    for i in range(1, len(indices)):
        if indices[i] == indices[i - 1] + 1:
            # This is part of the current block
            current_block.append(indices[i])

            # If the current block has reached 20 nodes, start a new block
            if len(current_block) == 20:
                blocks.append(current_block)
                current_block = []
        else:
            # This is the start of a new block
            if current_block:
                blocks.append(current_block)
            current_block = [indices[i]]

    # Add the last block if it's not empty
    if current_block:
        blocks.append(current_block)

    # Check that each block has at most 20 nodes
    for block in blocks:
        assert len(block) <= 20

    # Check that we have approximately 50 blocks (might be fewer if we couldn't get 50 full blocks)
    assert len(blocks) <= 50


def test_fallback_behavior() -> None:
    """Test the fallback behavior when we can't get enough blocks."""
    # Create a special case where we can't get 50 blocks of 20
    # For example, if we have 1100 nodes, we can only get 55 blocks of 20
    # But we need to ensure we still get 1000 nodes

    indexer = SummaryIndexer(
        data_source_id=1,
        splitter=SentenceSplitter(),
        llm=LLM.get_noop(),
        embedding_model=Embedding.get_noop(),
    )

    # Create a list of 1100 nodes
    nodes = [TextNode(text=f"Node {i}") for i in range(1100)]

    # Mock the random.sample function to return fewer than 50 indices
    # This simulates the case where we can't get 50 blocks
    original_sample = random.sample

    def mock_sample(population, k):
        # Return only 10 indices, which would give us 200 nodes (10 blocks of 20)
        return original_sample(population, min(k, 10))

    # Apply the mock
    random.sample = mock_sample

    try:
        # Sample the nodes
        sampled_nodes = indexer.sample_nodes(nodes)

        # Verify that we get 1000 nodes (fallback to first 1000)
        assert len(sampled_nodes) == 1000

        # Verify that these are the first 1000 nodes
        expected_nodes = nodes[:1000]
        assert sampled_nodes == expected_nodes
    finally:
        # Restore the original random.sample function
        random.sample = original_sample
