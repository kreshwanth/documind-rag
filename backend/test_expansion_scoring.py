import uuid
from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service
import re
import math
from collections import Counter
import numpy as np

db = SessionLocal()
user_id = uuid.UUID("f1a2138d-cf4a-4152-b51b-8a966911dd11")
leave_doc_id = uuid.UUID("42ac4238-1685-4a0f-8015-f5f492764398")
user = db.query(User).filter(User.id == user_id).first()

q = "An employee wants to take a long break to pursue further education that is relevant to their current job. What provision in the company’s leave policy could apply to them, and what approval would be required?"

# Query expansion / concept synonyms
CONCEPT_SYNONYMS = {
    'education': ['qualification', 'qualifications', 'enhance', 'degree', 'study', 'studies'],
    'break': ['sabbatical', 'sabbatical leave', 'one year', 'extended'],
    'long break': ['sabbatical', 'sabbatical leave', 'one year', 'extended leave'],
    'further education': ['enhance qualifications', 'qualifications relevant'],
    'relevant': ['relevant to their jobs', 'relevant to their job'],
    'approval': ['recommendations', 'hod', 'head of hr', 'ceo', 'final approval', 'director or ceo', 'reporting manager'],
    'no balance': ['leave without pay', 'zero or negative', 'lwp'],
    'joining': ['proportionally', 'remaining that year', 'date of joining', 'start of the calendar year']
}

def expand_query_terms(raw_q):
    q_low = raw_q.lower()
    terms = set(re.findall(r'\b[a-z]{3,}\b', q_low))
    for concept, syns in CONCEPT_SYNONYMS.items():
        if concept in q_low or any(w in q_low for w in concept.split() if len(w) > 3):
            for s in syns:
                for sw in re.findall(r'\b[a-z]{3,}\b', s):
                    terms.add(sw)
    return terms

all_terms = expand_query_terms(q)
print("Expanded query terms:", all_terms)

chunks = (
    db.query(DocumentChunk)
    .filter(DocumentChunk.document_id == leave_doc_id)
    .all()
)

for c in chunks:
    c_words = set(re.findall(r'\b[a-z]{3,}\b', c.content.lower()))
    matched = all_terms.intersection(c_words)
    print(f"Chunk #{c.chunk_index} (Page {c.page_number}) | Matched {len(matched)}: {matched}")
    if c.chunk_index in [8, 9]:
        print(f"  --> {c.content[:140]}")
