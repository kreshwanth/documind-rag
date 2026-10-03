import uuid
from app.services.citation_formatter import citation_formatter

def test_citation_formatting_and_deduplication():
    doc_id = uuid.uuid4()
    chunks = [
        {
            "chunk_id": uuid.uuid4(),
            "document_id": doc_id,
            "document_name": "Compliance.pdf",
            "page_number": 3,
            "chunk_index": 1,
            "similarity_score": 0.72,
            "content": "Compliance guideline snippet A."
        },
        {
            "chunk_id": uuid.uuid4(),
            "document_id": doc_id,
            "document_name": "Compliance.pdf",
            "page_number": 3,
            "chunk_index": 1,
            "similarity_score": 0.88,  # higher score for duplicate
            "content": "Compliance guideline snippet A."
        },
        {
            "chunk_id": uuid.uuid4(),
            "document_id": doc_id,
            "document_name": "Policy.docx",
            "page_number": None,
            "chunk_index": 0,
            "similarity_score": 0.94,
            "content": "Remote work policy."
        }
    ]
    citations = citation_formatter.format_citations(chunks)
    assert len(citations) == 2
    # Highest score first
    assert citations[0].similarity_score == 0.94
    assert citations[0].document_name == "Policy.docx"
    assert citations[0].page_number is None
    # Duplicate resolved with higher score
    assert citations[1].similarity_score == 0.88
