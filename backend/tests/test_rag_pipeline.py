import uuid
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service
from app.services.prompt_builder import FALLBACK_RESPONSE_STRING

def test_rag_fallback_on_unsupported_question(client, auth_headers_user1):
    payload = {
        "question": "What were the sales figures for Mars division in 2099?",
        "top_k": 3,
        "similarity_threshold": 0.60
    }
    response = client.post("/api/chat", json=payload, headers=auth_headers_user1)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == FALLBACK_RESPONSE_STRING
    assert data["is_fallback"] is True
    assert len(data["sources"]) == 0
    assert "conversation_id" in data

def test_conversations_crud(client, auth_headers_user1):
    # Create conversation
    create_res = client.post(
        "/api/conversations",
        json={"title": "Enterprise Security Review"},
        headers=auth_headers_user1
    )
    assert create_res.status_code == 201
    conv = create_res.json()
    conv_id = conv["id"]

    # List
    list_res = client.get("/api/conversations", headers=auth_headers_user1)
    assert list_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_res.json())

    # Get details
    detail_res = client.get(f"/api/conversations/{conv_id}", headers=auth_headers_user1)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Enterprise Security Review"

    # Delete
    del_res = client.delete(f"/api/conversations/{conv_id}", headers=auth_headers_user1)
    assert del_res.status_code == 200

def test_semantic_search_endpoint(client, auth_headers_user1):
    search_payload = {
        "query": "cloud infrastructure security",
        "top_k": 3,
        "similarity_threshold": 0.40
    }
    res = client.post("/api/search", json=search_payload, headers=auth_headers_user1)
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "cloud infrastructure security"
    assert "results" in data
