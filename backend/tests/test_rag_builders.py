import uuid
from app.services.context_builder import ContextBuilder, context_builder
from app.services.prompt_builder import PromptBuilder, prompt_builder, FALLBACK_RESPONSE_STRING

def test_context_builder_formatting():
    chunks = [
        {
            "chunk_id": uuid.uuid4(),
            "document_name": "Q3_Report.pdf",
            "page_number": 4,
            "chunk_index": 2,
            "content": "Gross margin increased by 14% year over year."
        },
        {
            "chunk_id": uuid.uuid4(),
            "document_name": "Handbook.docx",
            "page_number": None,
            "chunk_index": 0,
            "content": "Employees receive 20 days paid leave."
        }
    ]
    context = context_builder.build_context(chunks)
    assert "Q3_Report.pdf" in context
    assert "Page 4" in context
    assert "Handbook.docx" in context
    assert "Document Body" in context

def test_context_builder_deduplication():
    duplicate_chunks = [
        {"content": "Repeated policy text on security protocols.", "document_name": "Policy.pdf", "page_number": 1},
        {"content": "Repeated policy text on security protocols.", "document_name": "Policy.pdf", "page_number": 1}
    ]
    context = context_builder.build_context(duplicate_chunks)
    assert context.count("Repeated policy text") == 1

def test_prompt_builder():
    context = "Contextual snippet about AI."
    question = "How does AI work?"
    prompt = prompt_builder.build_rag_prompt(context, question)
    
    assert "=== DOCUMENT CONTEXT ===" in prompt
    assert context in prompt
    assert "=== USER QUESTION ===" in prompt
    assert question in prompt
    assert FALLBACK_RESPONSE_STRING in prompt
