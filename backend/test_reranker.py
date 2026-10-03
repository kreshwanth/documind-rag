import math
import re
from collections import Counter
import numpy as np

from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service
import uuid

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
user = db.query(User).filter(User.id == user_id).first()

q = "An employee wants to take a long break to pursue further education that is relevant to their current job. What provision in the company’s leave policy could apply to them, and what approval would be required?"

# Concept Synonym Mapping for Semantic Expansion
SEMANTIC_EXPANSIONS = {
    'education': ['qualification', 'qualifications', 'degree', 'study', 'enhance', 'academic', 'course'],
    'break': ['sabbatical', 'sabbatical leave', 'leave of absence', 'extended', 'unpaid'],
    'long break': ['sabbatical', 'sabbatical leave', 'one year', 'extended leave'],
    'further education': ['enhance qualifications', 'qualifications relevant', 'higher education'],
    'relevant': ['relevant to their jobs', 'relevant to their job', 'relevant to their duties'],
    'approval': ['approval', 'recommendations', 'hod', 'head of hr', 'ceo', 'permission', 'final approval', 'reporting manager'],
    'child': ['maternity', 'paternity', 'childbirth', 'adoption', 'pregnancy'],
    'illness': ['sick', 'doctor certificate', 'medical', 'sickness'],
    'money': ['encashment', 'encashed', 'paid', 'unpaid', 'salary']
}

all_chunks = (
    db.query(DocumentChunk, Document.original_filename, Document.id)
    .join(Document, DocumentChunk.document_id == Document.id)
    .filter(Document.user_id == user_id, Document.status == "completed", Document.id == leave_doc_id)
    .all()
)

print(f"Total chunks in Leave Policy: {len(all_chunks)}")

# Reranker Prototype
def score_chunk(chunk, query_text):
    c_text = chunk.content.lower()
    q_text = query_text.lower()
    
    score = 0.0
    
    # 1. Direct query terms
    q_words = re.findall(r'\b[a-z]{3,}\b', q_text)
    for qw in q_words:
        if qw in c_text:
            score += 1.5
            
    # 2. Semantic Synonyms / Concepts
    for concept, synonyms in SEMANTIC_EXPANSIONS.items():
        if concept in q_text or any(cw in q_text for cw in concept.split()):
            for syn in synonyms:
                if syn in c_text:
                    score += 4.0
                    
    # 3. Actionable Rule Indicators
    if any(ind in c_text for ind in ['can take a sabbatical', 'provided they have', 'hod should send recommendations', 'head of hr for the ceo', 'continuous service']):
        score += 8.0
        
    # 4. Penalty for generic boilerplate introductory chunks
    if any(bp in c_text for bp in ['purpose\neligibility\nscope', 'describes the guidelines for employees requesting', 'value and provide our employees']):
        score -= 10.0
        
    return score

scored = [(score_chunk(c, q), c) for c, _, _ in all_chunks]
scored.sort(key=lambda x: x[0], reverse=True)

print("\n=== RERANKED RESULTS ===")
for sc, c in scored[:5]:
    print(f"Chunk #{c.chunk_index} (Page {c.page_number}) | Score: {sc:.2f}")
    print(c.content[:160])
    print("-" * 50)
