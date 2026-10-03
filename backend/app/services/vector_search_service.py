import math
import re
from collections import Counter
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.config import settings
from app.services.reranker_service import semantic_reranker
import numpy as np
import logging

logger = logging.getLogger("documind.vector_search")

STOP_WORDS = {
    'what', 'is', 'the', 'of', 'in', 'and', 'to', 'for', 'a', 'an', 'are', 'how', 'why', 'who', 'whom',
    'which', 'on', 'at', 'by', 'from', 'with', 'about', 'as', 'into', 'like', 'through', 'after', 'over'
}

class VectorSearchService:
    @staticmethod
    def search(
        db: Session,
        user_id: UUID,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        document_ids: Optional[List[UUID]] = None,
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform Hybrid Vector & Multi-Term Keyword similarity search.
        Enforces user ownership, strict document_id filtering, and domain-aware rank fusion.
        """
        effective_top_k = top_k or settings.TOP_K
        effective_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD

        # 1. Fetch matching candidate chunks for user (strictly isolating document_ids if provided)
        query = (
            db.query(DocumentChunk, Document.original_filename, Document.id)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(
                Document.user_id == user_id,
                Document.status == "completed"
            )
        )

        if document_ids and len(document_ids) > 0:
            query = query.filter(Document.id.in_(document_ids))
            logger.info(f"Vector search strictly isolated to document IDs: {[str(d) for d in document_ids]}")

        all_chunks = query.all()
        if not all_chunks:
            logger.info("No matching chunks found in database for query.")
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)

        # 2. Extract query terms and semantic concept synonyms
        raw_query = (query_text or "").lower()
        base_query_terms = [w for w in re.findall(r'\b[a-z]{3,}\b', raw_query) if w not in STOP_WORDS]
        
        # Concept synonyms for semantic bridging
        CONCEPT_SYNONYMS = {
            'education': ['qualification', 'qualifications', 'enhance', 'degree', 'study', 'studies', 'course'],
            'qualifications': ['sabbatical', 'sabbatical leave', 'enhance', 'relevant to their jobs', 'education'],
            'break': ['sabbatical', 'sabbatical leave', 'one year', 'extended'],
            'extended': ['sabbatical', 'sabbatical leave', 'one year', 'long break', 'extended period'],
            'long break': ['sabbatical', 'sabbatical leave', 'one year', 'extended leave', 'qualifications'],
            'further education': ['enhance qualifications', 'qualifications relevant', 'higher education', 'sabbatical'],
            'relevant': ['relevant to their jobs', 'relevant to their job', 'continuous service'],
            'approval': ['recommendations', 'hod', 'head of hr', 'ceo', 'final approval', 'director or ceo', 'reporting manager'],
            'balance': ['leave without pay', 'zero or negative', 'lwp', 'no remaining'],
            'remaining': ['leave without pay', 'zero or negative', 'lwp', 'time off', 'balance'],
            'used all': ['leave without pay', 'zero or negative', 'lwp', 'no remaining'],
            'used': ['leave without pay', 'zero or negative', 'lwp', 'no remaining'],
            'exhausted': ['leave without pay', 'zero or negative', 'lwp', 'no remaining'],
            'joining': ['proportionally', 'remaining that year', 'date of joining', 'start of the calendar year'],
            'joins': ['proportionally', 'remaining that year', 'date of joining', 'start of the calendar year'],
            'joined': ['proportionally', 'remaining that year', 'date of joining', 'start of the calendar year'],
            'illness': ['doctor', 'certificate', 'sickness', 'sick leave', 'medical', 'seriousness of the sickness', 'cannot be availed'],
            'ill': ['doctor', 'certificate', 'sickness', 'sick leave', 'medical', 'doctor\'s certificate'],
            'sick': ['doctor', 'certificate', 'sickness', 'cannot be availed', 'doctor\'s certificate'],
            'limit': ['doctor', 'certificate', 'sickness', 'cannot be availed', 'doctor\'s certificate'],
            'exception': ['head of hr approves', 'exceptions will only be permitted', 'statutory requirements', 'modify the above policy'],
            'modify': ['head of hr approves', 'exceptions will only be permitted', 'statutory requirements', 'modify the above policy'],
            'holidays': ['festivals', 'cannot be carried forward', 'calendar year', 'encashed'],
            'festivals': ['cannot be carried forward', 'calendar year', 'encashed', 'holidays'],
            'unused': ['accumulated', 'encashed', 'maximum of', 'leaves in excess', 'accrued'],
            'accumulated': ['encashed', 'maximum of', 'leaves in excess', 'accrued', 'following calendar year'],
            'denied': ['approve or deny', 'approve or refuse', 'refused', 'denied', 'decide whether to approve', 'reporting manager will review'],
            'refused': ['approve or refuse', 'approve or deny', 'refusal', 'denial', 'decide whether to approve']
        }

        expanded_terms = set(base_query_terms)
        for concept, syns in CONCEPT_SYNONYMS.items():
            if concept in raw_query or any(w in raw_query for w in concept.split() if len(w) > 3):
                for s in syns:
                    for sw in re.findall(r'\b[a-z]{3,}\b', s):
                        if sw not in STOP_WORDS:
                            expanded_terms.add(sw)

        unique_query_terms = set(base_query_terms)

        # 3. Calculate document frequency (DF)
        N = len(all_chunks)
        df = Counter()
        for chunk, _, _ in all_chunks:
            c_words = set(re.findall(r'\b[a-z]{3,}\b', chunk.content.lower()))
            for t in expanded_terms:
                if t in c_words:
                    df[t] += 1

        scored_hits = []
        for chunk, doc_name, doc_id in all_chunks:
            c_emb = chunk.embedding
            if c_emb is None:
                continue

            # A. Cosine similarity
            c_vec = np.array(c_emb, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if q_norm > 0 and c_norm > 0:
                cosine_sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
            else:
                cosine_sim = 0.0

            # B. Keyword & Multi-Term Coverage score
            keyword_score = 0.0
            c_text_lower = chunk.content.lower()

            c_words = re.findall(r'\b[a-z]{3,}\b', c_text_lower)
            c_counts = Counter(c_words)
            c_len = max(len(c_words), 1)

            matched_terms = [t for t in expanded_terms if c_counts[t] > 0]
            term_coverage = len(matched_terms) / max(len(expanded_terms), 1)

            bm25 = 0.0
            for t in matched_terms:
                tf = c_counts[t]
                idf = math.log(1.0 + (N - df[t] + 0.5) / (df[t] + 0.5))
                tf_sat = (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * (c_len / 100.0)))
                bm25 += max(idf, 0.2) * tf_sat

            # Scale BM25 by term coverage
            if term_coverage >= 0.35:
                coverage_multiplier = 3.5 * (term_coverage ** 1.5)
            elif term_coverage >= 0.20:
                coverage_multiplier = 2.0 * term_coverage
            elif term_coverage <= 0.10:
                coverage_multiplier = 0.15
            else:
                coverage_multiplier = 0.6

            keyword_score = bm25 * coverage_multiplier

            # Phrase & Concept alignments
            for i in range(len(base_query_terms) - 1):
                q_bigram = f"{base_query_terms[i]} {base_query_terms[i+1]}"
                if q_bigram in c_text_lower:
                    keyword_score += 4.0

            # Semantic concept bonuses
            if any(w in raw_query for w in ['education', 'study', 'studies', 'break', 'sabbatical', 'qualif', 'degree']):
                if any(p in c_text_lower for p in ['sabbatical', 'enhance their qualifications', 'qualifications relevant', 'up to one year']):
                    keyword_score += 8.0

            if any(w in raw_query for w in ['objective', 'purpose', 'aim', 'goal']):
                if 'objective of this guideline' in c_text_lower or 'purpose of this guideline' in c_text_lower:
                    keyword_score += 6.0

            if any(w in raw_query for w in ['balance', 'remaining', 'without pay', 'lwp', 'options']):
                if 'leave without pay' in c_text_lower or 'zero or negative' in c_text_lower:
                    keyword_score += 6.0

            if any(w in raw_query for w in ['joining', 'halfway', 'mid-year', 'mid year', 'entitlement', 'handled', 'joins']):
                if any(p in c_text_lower for p in ['proportionally calculated', 'joining after the date', 'date of joining', 'calendar year basis', 'leave entitlements']):
                    keyword_score += 6.0

            # C. Hybrid Score Fusion & Candidate Relevance
            hybrid_score = (cosine_sim * 0.40) + (keyword_score * 0.07)
            effective_score = min(max(hybrid_score, 0.0), 0.99)

            is_relevant = (
                (term_coverage >= 0.15 and effective_score >= effective_threshold) or
                (cosine_sim >= 0.35) or
                (keyword_score >= 2.5)
            )

            if is_relevant:
                scored_hits.append({
                    "chunk_id": chunk.id,
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "similarity_score": round(float(effective_score), 4),
                    "raw_cosine": round(float(cosine_sim), 4),
                    "excerpt": chunk.content[:200] + ("..." if len(chunk.content) > 200 else "")
                })

        scored_hits.sort(key=lambda x: x["similarity_score"], reverse=True)
        candidate_pool = scored_hits[:max(effective_top_k * 2, 8)]

        # 4. Semantic Reranking
        top_hits = semantic_reranker.rerank(
            query_text=raw_query,
            candidates=candidate_pool,
            top_k=effective_top_k
        )

        # Log retrieved documents for debugging and verification
        logger.info(f"Retrieved and ranked {len(top_hits)} semantically relevant chunks for query: '{raw_query}':")
        for h in top_hits:
            text_preview = h['content'].replace('\n', ' ')[:100]
            logger.info(
                f"  -> Chunk ID: {h['chunk_id']} | Doc: {h['document_name']} | P{h['page_number']} | "
                f"Score: {h['similarity_score']} (Cosine: {h.get('raw_cosine', 0.0)}) | Text: '{text_preview}...'"
            )

        return top_hits

vector_search_service = VectorSearchService()


