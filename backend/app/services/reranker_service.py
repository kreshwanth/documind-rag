import re
from typing import List, Dict, Any

class SemanticReranker:
    """
    Reranker that evaluates candidate chunks based on:
    1. Semantic Concept & Intent Alignment (handling indirect questions like 'further education' -> 'qualifications')
    2. Policy Provision & Actionable Rule Density
    3. Suppression of generic boilerplate / introductory scope
    4. Exact phrasing & compound relation matches
    """

    SEMANTIC_CONCEPT_MAP = [
        # Education & Sabbatical Leave
        {
            "query_patterns": [r'\b(education|study|degree|academic|course|further education|higher studies|upskill|qualif)\b'],
            "chunk_patterns": [r'\b(enhance their qualifications|qualifications relevant|sabbatical|sabbatical leave)\b'],
            "weight": 8.0
        },
        {
            "query_patterns": [r'\b(long break|career break|break from work|extended break|take a break|time off for)\b'],
            "chunk_patterns": [r'\b(sabbatical|sabbatical leave|up to one year|extended leave)\b'],
            "weight": 7.0
        },
        {
            "query_patterns": [r'\b(relevant to|related to|current job|their job|their duties)\b'],
            "chunk_patterns": [r'\b(relevant to their jobs|relevant to their job|continuous service)\b'],
            "weight": 6.0
        },
        {
            "query_patterns": [r'\b(approval|permission|who approves|process|authority)\b'],
            "chunk_patterns": [r'\b(hod should send recommendations|head of hr for the ceo|reporting manager|director or ceo|final approval)\b'],
            "weight": 6.0
        },
        # Zero balance & Leave Without Pay
        {
            "query_patterns": [r'\b(no balance|zero balance|negative balance|no remaining|exhausted|out of leave)\b'],
            "chunk_patterns": [r'\b(leave without pay|zero or negative|lwp)\b'],
            "weight": 8.0
        },
        # Joining date / Mid-year
        {
            "query_patterns": [r'\b(halfway|mid-year|mid year|joins|joining|date of joining)\b'],
            "chunk_patterns": [r'\b(proportionally calculated|joining after the date|date of joining|calendar year basis)\b'],
            "weight": 8.0
        },
        # Objective / Goals
        {
            "query_patterns": [r'\b(objective|purpose|goal|aim|why was this)\b'],
            "chunk_patterns": [r'\b(objective of this guideline|purpose of this|aims to)\b'],
            "weight": 8.0
        },
        # Maternity / Paternity
        {
            "query_patterns": [r'\b(pregnant|pregnancy|childbirth|maternity|paternity|baby|adoption)\b'],
            "chunk_patterns": [r'\b(maternity leave|paternity leave|maternity benefit act|childbirth|adoption)\b'],
            "weight": 8.0
        },
        # Sick Leave / Illness / Medical Certificate
        {
            "query_patterns": [r'\b(illness|sick|sickness|medical|doctor|certificate|health|disease|unwell)\b'],
            "chunk_patterns": [r'\b(doctor\'s certificate|seriousness of the sickness|cannot be availed for more than|refer any employee to a doctor)\b'],
            "weight": 8.0
        },
        # Approval / Denial / Refusal / Rejection Process
        {
            "query_patterns": [r'\b(denied|refused|rejected|deny|refuse|reject|approval process|decision|refusal|denial)\b'],
            "chunk_patterns": [r'\b(approve or deny|approve or refuse|decide whether to approve|if the leave is approved|review the request)\b'],
            "weight": 8.0
        }
    ]

    GENERIC_BOILERPLATE_PATTERNS = [
        r'purpose\s+eligibility\s+scope',
        r'at\s+["“\']?name of the company["”\']?',
        r'describes the guidelines for employees requesting',
        r'all rights reserved',
        r'table of contents'
    ]

    @classmethod
    def rerank(cls, query_text: str, candidates: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
        """Reranks candidate chunks using semantic intent expansion and rule density scoring."""
        if not candidates:
            return []

        q_lower = query_text.lower()
        q_words = set(re.findall(r'\b[a-z]{3,}\b', q_lower))

        reranked = []
        for item in candidates:
            c_content = item["content"].lower()
            base_sim = float(item.get("similarity_score", 0.0))
            raw_cosine = float(item.get("raw_cosine", 0.0))

            rerank_score = (base_sim * 0.4) + (raw_cosine * 0.3)

            # 1. Semantic Concept Matching
            for mapping in cls.SEMANTIC_CONCEPT_MAP:
                q_matched = any(re.search(pat, q_lower) for pat in mapping["query_patterns"])
                if q_matched:
                    c_matched = any(re.search(pat, c_content) for pat in mapping["chunk_patterns"])
                    if c_matched:
                        rerank_score += mapping["weight"]

            # 2. Actionable Rule / Provision Density
            if any(cue in c_content for cue in ['provided they have', 'can take a', 'shall be entitled', 'must submit', 'will receive their', 'is required']):
                rerank_score += 2.0

            # 3. Suppress generic introductory boilerplate
            for bp in cls.GENERIC_BOILERPLATE_PATTERNS:
                if re.search(bp, c_content):
                    # Only penalize if query didn't specifically ask for company purpose/scope
                    if not any(w in q_lower for w in ['scope', 'purpose of the policy', 'who is eligible', 'eligibility']):
                        rerank_score -= 10.0

            # Compute normalized rerank score
            item_copy = dict(item)
            item_copy["rerank_score"] = round(rerank_score, 4)
            reranked.append(item_copy)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]

semantic_reranker = SemanticReranker()
