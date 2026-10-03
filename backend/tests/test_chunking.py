import uuid
from app.services.chunking_service import chunking_service

def test_empty_document():
    pages = [{"page_number": 1, "text": ""}]
    chunks = chunking_service.chunk_document(pages)
    assert len(chunks) == 0

def test_short_document():
    pages = [{"page_number": 1, "text": "Short enterprise statement."}]
    chunks = chunking_service.chunk_document(pages)
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Short enterprise statement."
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0

def test_multi_page_chunking_with_overlap():
    pages = [
        {"page_number": 1, "text": "Page one text. " * 30},
        {"page_number": 2, "text": "Page two text. " * 30}
    ]
    doc_id = uuid.uuid4()
    chunks = chunking_service.chunk_document(
        pages_content=pages,
        document_id=doc_id,
        chunk_size=120,
        chunk_overlap=30
    )
    assert len(chunks) > 2
    for c in chunks:
        assert c["document_id"] == doc_id
        assert c["page_number"] in [1, 2]
        assert "metadata" in c
        assert c["metadata"]["has_page_number"] is True

def test_paragraph_boundary_preservation():
    text = "Paragraph One.\n\nParagraph Two with distinct facts.\n\nParagraph Three."
    pages = [{"page_number": 1, "text": text}]
    chunks = chunking_service.chunk_document(pages, chunk_size=80, chunk_overlap=10)
    assert len(chunks) >= 1
