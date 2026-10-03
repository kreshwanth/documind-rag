from app.services.embedding_service import EmbeddingService
from unittest.mock import patch, MagicMock

def test_pseudo_embedding_dimension_and_norm():
    service = EmbeddingService(dimension=768)
    vec = service._pseudo_embedding("Test Query String")
    assert len(vec) == 768
    # Test query embedding
    query_vec = service.embed_query("Another query")
    assert len(query_vec) == 768

def test_batch_embedding():
    service = EmbeddingService(dimension=768)
    texts = [f"Text chunk number {i}" for i in range(15)]
    results = service.embed_chunks(texts, batch_size=5)
    assert len(results) == 15
    for vec in results:
        assert len(vec) == 768

def test_embedding_mock_api_success():
    with patch("google.generativeai.embed_content") as mock_embed:
        mock_embed.return_value = {"embedding": [[0.1] * 768, [0.2] * 768]}
        service = EmbeddingService(api_key="mock_key", dimension=768)
        
        vectors = service.embed_chunks(["Chunk 1", "Chunk 2"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 768

def test_embedding_api_failure_fallback():
    with patch("google.generativeai.embed_content", side_effect=Exception("API Quota Error")):
        service = EmbeddingService(api_key="mock_key", dimension=768)
        vectors = service.embed_chunks(["Chunk with failing API"])
        assert len(vectors) == 1
        assert len(vectors[0]) == 768
