import io
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service

def test_document_upload_and_cross_user_authorization(client, auth_headers_user1, auth_headers_user2, db_session, test_user):
    # User 1 uploads a TXT document
    content = b"DocuMind Enterprise Architecture Document. Page 1 Content.\n\nSection 2: Security & Isolation."
    files = {"file": ("enterprise_plan.txt", io.BytesIO(content), "text/plain")}

    upload_res = client.post("/api/documents/upload", files=files, headers=auth_headers_user1)
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["original_filename"] == "enterprise_plan.txt"
    assert doc_data["status"] == "pending"

    # Check status endpoint
    status_res = client.get(f"/api/documents/{doc_id}/status", headers=auth_headers_user1)
    assert status_res.status_code == 200
    assert status_res.json()["id"] == doc_id

    # User 1 can list the document
    list_res1 = client.get("/api/documents", headers=auth_headers_user1)
    assert list_res1.status_code == 200
    assert any(d["id"] == doc_id for d in list_res1.json())

    # User 2 MUST NOT see User 1's document in list (Tenant Isolation)
    list_res2 = client.get("/api/documents", headers=auth_headers_user2)
    assert list_res2.status_code == 200
    assert not any(d["id"] == doc_id for d in list_res2.json())

    # User 2 MUST NOT access User 1's document details (404)
    get_res2 = client.get(f"/api/documents/{doc_id}", headers=auth_headers_user2)
    assert get_res2.status_code == 404

    # User 2 MUST NOT delete User 1's document (404)
    del_res2 = client.delete(f"/api/documents/{doc_id}", headers=auth_headers_user2)
    assert del_res2.status_code == 404

    # User 1 CAN delete their own document
    del_res1 = client.delete(f"/api/documents/{doc_id}", headers=auth_headers_user1)
    assert del_res1.status_code == 200

def test_upload_invalid_file_extension(client, auth_headers_user1):
    files = {"file": ("malicious.exe", io.BytesIO(b"executable"), "application/x-msdownload")}
    res = client.post("/api/documents/upload", files=files, headers=auth_headers_user1)
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]

def test_upload_empty_file(client, auth_headers_user1):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    res = client.post("/api/documents/upload", files=files, headers=auth_headers_user1)
    assert res.status_code == 400
    assert "Cannot upload an empty file" in res.json()["detail"]
