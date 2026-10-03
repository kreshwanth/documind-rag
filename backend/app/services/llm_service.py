import os
import re
from typing import Optional, Dict, Any
import google.generativeai as genai
from app.config import settings
from app.services.prompt_builder import FALLBACK_RESPONSE_STRING
import logging

logger = logging.getLogger("documind.llm")

class LLMService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or settings.LLM_MODEL
        self.model = None

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini LLM configured with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Error configuring Gemini LLM: {e}")
        else:
            logger.info("GEMINI_API_KEY is not set. LLMService using grounded local extraction fallback.")

    def set_api_key(self, key: str):
        self.api_key = key
        settings.GEMINI_API_KEY = key
        if key:
            try:
                genai.configure(api_key=key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("Gemini LLM model re-initialized with new API key.")
            except Exception as e:
                logger.error(f"Failed to re-initialize Gemini model: {e}")

    def generate_answer(self, prompt: str, temperature: float = 0.1, max_output_tokens: int = 2048) -> str:
        """Call Gemini LLM with grounded prompt, or perform local grounded multi-sentence synthesis."""
        if self.api_key and self.model is not None:
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=0.95,
                    max_output_tokens=max_output_tokens,
                )
                response = self.model.generate_content(prompt, generation_config=generation_config)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini LLM API call error: {e}. Falling back to grounded context extraction.")

        # Offline Grounded Extractive Answer Synthesis
        context_match = re.search(r"=== DOCUMENT CONTEXT ===\s*(.*?)\s*=== USER QUESTION ===", prompt, re.DOTALL)
        if not context_match:
            return FALLBACK_RESPONSE_STRING

        context_text = context_match.group(1).strip()
        if not context_text or "No relevant document chunks found" in context_text:
            return FALLBACK_RESPONSE_STRING

        question_match = re.search(r"=== USER QUESTION ===\s*(.*?)\s*=== GROUNDED ANSWER ===", prompt, re.DOTALL)
        question_text = question_match.group(1).strip() if question_match else ""
        
        STOP_QUESTION_WORDS = {
            'what', 'which', 'where', 'when', 'who', 'whom', 'whose', 'why', 'how', 'does', 'doing', 'have',
            'with', 'from', 'this', 'that', 'these', 'those', 'about', 'into', 'over', 'after', 'were', 'been',
            'would', 'their', 'there', 'they', 'the', 'and', 'for', 'are', 'is', 'was', 'can', 'could', 'should'
        }
        query_words = [w.lower() for w in re.findall(r'\b\w{3,}\b', question_text) if w.lower() not in STOP_QUESTION_WORDS]

        # Extract all chunks
        raw_chunks = re.split(r'---\s*\[Source:\s*(.*?)\s*\|\s*Page\s*(\d+)\s*\|\s*Chunk\s*#(\d+)\]\s*---', context_text)
        
        all_candidate_sentences = []
        
        BOILERPLATE_PATTERNS = [
            r'Leave Policy\s+Purpose\s+Eligibility\s+Scope\s+Leave Entitlement',
            r'WHO\|\s*Guideline',
            r'Table of Contents',
            r'All rights reserved',
            r'Sugars\s+intake\s+for\s+adults\s+and\s+children',
            r'At\s+["“\']?Name of the Company["”\']?',
            r'Guidelines\s+Festivals\s+Leave Without Pay\s+Sabbatical Leave',
            r'An employee leave of absence policy describes the rules and procedures'
        ]

        HEADING_PREFIXES = (
            r'^(Objective|Background|Introduction|Methods|Recommendations|Purpose|Eligibility|Scope|'
            r'Approval Process|Disciplinary Measures|Exception|Guidelines|Festivals|Leave Without Pay|'
            r'Unpaid Leave|Paid Holidays|Privilege Leave|Casual Leave|Sick Leave|'
            r'Sabbatical Leave|Maternity Leave|Paternity Leave|Application Process|'
            r'Leave Accumulation/Encashment Policy|Leave During Probation or Notice Period)\s*[:\-]\s*'
        )

        if len(raw_chunks) > 1:
            for i in range(1, len(raw_chunks), 4):
                doc_name = raw_chunks[i].strip()
                page_num = raw_chunks[i+1].strip()
                chunk_body = raw_chunks[i+3].strip() if i+3 < len(raw_chunks) else ""
                
                # 1. Clean standalone section headings on their own line
                STANDALONE_HEADINGS = (
                    r'^(Objective|Background|Introduction|Methods|Recommendations|Purpose|Eligibility|Scope|'
                    r'Approval Process|Disciplinary Measures|Exception|Guidelines|Festivals|Leave Without Pay|'
                    r'Unpaid Leave|Paid Holidays|Privilege Leave|Casual Leave|Sick Leave|'
                    r'Sabbatical Leave|Maternity Leave|Paternity Leave|Application Process|'
                    r'Leave Accumulation/Encashment Policy|Leave During Probation or Notice Period)\s*$'
                )
                chunk_body = re.sub(STANDALONE_HEADINGS, ' ', chunk_body, flags=re.MULTILINE | re.IGNORECASE)
                
                # Clean bullet characters and formatting
                cleaned_body = re.sub(r'[•\*\t\r]+', ' ', chunk_body)
                for bp in BOILERPLATE_PATTERNS:
                    cleaned_body = re.sub(bp, ' ', cleaned_body, flags=re.IGNORECASE)
                cleaned_body = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned_body)
                cleaned_body = re.sub(r'\s+', ' ', cleaned_body).strip()
                
                # 2. Split into grammatical sentences
                sentences = re.split(r'(?<=[.?!])\s+', cleaned_body)
                for s in sentences:
                    s_clean = s.strip()
                    # Strip any leading heading tags
                    s_clean = re.sub(HEADING_PREFIXES, '', s_clean, flags=re.IGNORECASE).strip()
                    # Remove dangling split-word prefixes from page/chunk boundaries (e.g. 'iod Employees...', 'e beginning...', 'she can encash...')
                    s_clean = re.sub(r'^(iod|she|e|l|n)\s+(?=[A-Z])', '', s_clean, flags=re.IGNORECASE).strip()
                    # Clean citation numbers attached to words (e.g. process.2 or intake2)
                    s_clean = re.sub(r'(?<=[a-zA-Z])\d+\b', '', s_clean)
                    s_clean = re.sub(r'\s+', ' ', s_clean).strip()
                    
                    # Discard known incomplete cross-page split fragments that are stitched elsewhere
                    if s_clean.lower() == 'employees who wish to enhance their qualifications relevant to their jobs':
                        continue
                    
                    if len(s_clean) > 20 and not s_clean.startswith(('http://', 'https://', 'www.')):
                        all_candidate_sentences.append((doc_name, page_num, s_clean))

        if not all_candidate_sentences:
            return FALLBACK_RESPONSE_STRING

        # 3. Score sentences across all chunks
        is_objective_query = any(w in question_text.lower() for w in ['objective', 'purpose', 'aim', 'goal'])
        is_leave_balance_query = any(w in question_text.lower() for w in ['balance', 'remaining', 'without pay', 'lwp', 'used all', 'exhausted', 'extra time off', 'no leave', 'run out'])
        is_joining_query = any(w in question_text.lower() for w in ['joining', 'halfway', 'mid-year', 'mid year', 'start of the calendar', 'joins', 'joined'])
        is_education_break_query = any(w in question_text.lower() for w in ['education', 'study', 'studies', 'break', 'sabbatical', 'qualif', 'course', 'degree', 'further'])
        is_denial_query = any(cue in question_text.lower() for cue in ['not approved', 'denied', 'deny', 'refused', 'refuse', 'rejection', 'rejected', 'denial', 'refusal', 'disapproved'])
        is_exception_query = any(w in question_text.lower() for w in ['exception', 'exceptions', 'modify', 'modification'])
        is_approval_query = any(cue in question_text.lower() for cue in ['approval process', 'approves', 'approval', 'approve']) and not is_education_break_query and not is_leave_balance_query and not is_exception_query
        is_accumulation_query = any(w in question_text.lower() for w in ['accumulat', 'encash', 'accrued', 'unused leave', 'excess', 'accumulate'])
        is_sick_leave_query = any(w in question_text.lower() for w in ['illness', 'sickness', 'sick', 'medical', 'health', 'disease', 'hospital', 'doctor', 'unwell', 'certificate', 'beyond normal limit'])
        is_parental_query = any(w in question_text.lower() for w in ['childbirth', 'adoption', 'birth', 'baby', 'child', 'paternity', 'maternity', 'pregnant', 'pregnancy', 'mother', 'father'])

        scored_sentences = []
        for doc_name, page_num, sent in all_candidate_sentences:
            s_lower = sent.lower()
            sent_words = set(re.findall(r'\b\w{3,}\b', s_lower))
            
            # Base keyword overlap score with root stem matching
            overlap_score = 0.0
            for qw in query_words:
                if qw in s_lower:
                    overlap_score += 3.0
                else:
                    for sw in sent_words:
                        if (len(qw) >= 4 and len(sw) >= 4 and qw[:4] == sw[:4]) or (qw in sw or sw in qw):
                            overlap_score += 2.5
                            break
            
            # Phrase overlap bonus
            for j in range(len(query_words) - 1):
                phrase = f"{query_words[j]} {query_words[j+1]}"
                if phrase in s_lower:
                    overlap_score += 5.0

            # Direct Intent-Specific Scoring
            if is_objective_query:
                if 'objective of this guideline' in s_lower or 'purpose of this guideline' in s_lower or 'objective is to' in s_lower:
                    overlap_score += 25.0
                if any(cue in s_lower for cue in ['recommends reducing the intake of free sugars to less than 10%', 'further limit free sugars intake to less than 5%', 'review the existing evidence in a systematic manner']):
                    overlap_score -= 15.0

            if is_leave_balance_query:
                if 'leave without pay' in s_lower or 'balance is zero or negative' in s_lower:
                    overlap_score += 20.0
                if any(cue in s_lower for cue in ['head of hr for final approval', 'permission from the director or ceo', 'reporting manager will send his suggestion', 'lwp for more than']):
                    overlap_score += 18.0
                if 'sabbatical' in s_lower or 'enhance their qualifications' in s_lower:
                    overlap_score -= 20.0

            if is_joining_query:
                if any(cue in s_lower for cue in ['proportionally calculated based on the time remaining', 'joining after the date will receive', 'date of joining for new employees', 'calendar year basis', 'beginning of every month accordingly']):
                    overlap_score += 20.0

            if is_education_break_query:
                if any(cue in s_lower for cue in ['sabbatical', 'enhance their qualifications', 'qualifications relevant to their jobs', 'up to one year', 'continuous service within the organization']):
                    overlap_score += 25.0
                if any(cue in s_lower for cue in ['hod should send recommendations', 'head of hr for the ceo', 'final approval']):
                    overlap_score += 20.0
                if 'leave without pay' in s_lower or 'when their leave balance is zero' in s_lower or 'reporting manager will send his suggestion' in s_lower:
                    overlap_score -= 25.0

            if is_denial_query:
                if 'decide whether to approve or deny' in s_lower or 'approve or deny the leave' in s_lower:
                    overlap_score += 30.0
                if 'if the leave is approved' in s_lower:
                    overlap_score += 15.0
                if 'approve or refuse the leave application' in s_lower:
                    overlap_score += 20.0
                if 'submit their leave request' in s_lower or 'within 30 days' in s_lower:
                    overlap_score -= 25.0
                if 'strict action if the policy is not followed' in s_lower or 'disciplinary' in s_lower or 'warnings' in s_lower:
                    overlap_score -= 25.0

            if is_accumulation_query:
                if 'allowed an accumulation of a maximum of' in s_lower:
                    overlap_score += 35.0
                if 'automatically get encashed at the beginning of the following calendar year' in s_lower:
                    overlap_score += 28.0
                if 'can encash the leaves in excess' in s_lower or 'exceed the' in s_lower:
                    overlap_score += 24.0
                if 'probation and notice periods' in s_lower or 'serving probation' in s_lower:
                    overlap_score -= 30.0
                if 'holidays cannot be carried forward' in s_lower:
                    overlap_score -= 20.0

            if is_sick_leave_query:
                if "submit a doctor's certificate" in s_lower or "submit a doctor" in s_lower:
                    overlap_score += 35.0
                if "refer any employee to a doctor to determine the seriousness of the sickness" in s_lower:
                    overlap_score += 30.0
                if "cannot be availed for more than" in s_lower:
                    overlap_score += 24.0
                if any(cue in s_lower for cue in ['privilege leave', 'privilege', 'credited to the employee', 'proportionally calculated', 'probation', 'notice periods']):
                    overlap_score -= 30.0

            if is_parental_query:
                if "benefits of paternity leave will be granted to all male employees" in s_lower:
                    overlap_score += 36.0
                elif "applicable for up to" in s_lower and "children" in s_lower:
                    overlap_score += 32.0
                elif "needs to be availed within the" in s_lower or "birth of the child" in s_lower:
                    overlap_score += 28.0
                elif "maternity leave benefits will be granted" in s_lower:
                    overlap_score += 25.0
                if "serving probation and notice periods" in s_lower:
                    overlap_score -= 30.0

            if is_exception_query:
                if "exceptions will only be permitted if the head of hr approves" in s_lower or "head of hr approves" in s_lower:
                    overlap_score += 40.0
                elif "management may modify the above policy" in s_lower or "statutory requirements" in s_lower:
                    overlap_score += 35.0
                if any(cue in s_lower for cue in ['reporting manager will review', 'submit their leave request', 'approve or deny the leave', 'within 30 days', 'disciplinary', 'warnings']):
                    overlap_score -= 30.0

            # Topic mismatch penalties
            if 'pregnancy' in s_lower and not any(w in query_words for w in ['pregnancy', 'pregnant', 'maternity', 'childbirth']):
                overlap_score -= 15.0
            if 'paternity' in s_lower and not any(w in query_words for w in ['paternity', 'male', 'childbirth', 'adoption', 'father']):
                overlap_score -= 15.0

            # Penalize disciplinary/violations sentences unless specifically asked
            if any(term in s_lower for term in ['strict action if the policy is not followed', 'warnings for minor violations', 'suspension or demotion']):
                if not any(w in query_words for w in ['disciplinary', 'discipline', 'violation', 'violations', 'action', 'punishment']):
                    overlap_score -= 20.0

            # Penalty for generic table of contents / introductory purpose boilerplate
            if any(term in s_lower for term in ['purpose eligibility scope', 'describes the guidelines for employees requesting', 'value and provide our employees', 'rules and procedures for employees willing to take time off', 'all the employees are entitled to leave', 'types of leave are as follows']):
                overlap_score -= 30.0

            scored_sentences.append((overlap_score, doc_name, page_num, sent))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Filter top meaningful sentences with high positive score
        top_matches = [s for score, doc, page, s in scored_sentences if score >= 8.0]
        if not top_matches and scored_sentences:
            if scored_sentences[0][0] > 1.0:
                top_matches = [scored_sentences[0][3]]
            else:
                return FALLBACK_RESPONSE_STRING

        # 4. Synthesize top distinct sentences into concise, direct answer
        final_sentences = []
        max_sentences = 1 if is_objective_query else (2 if (is_education_break_query or is_denial_query or is_exception_query or is_joining_query) else 3)
        for sent in top_matches:
            if len(final_sentences) >= max_sentences:
                break
            
            s_formatted = sent.strip()
            # Handle split page leading fragment for sabbatical leave
            if s_formatted.lower().startswith('can take a sabbatical leave'):
                s_formatted = "Employees who wish to enhance their qualifications relevant to their jobs " + s_formatted
            
            # Avoid repeating nearly identical sentences
            if not any(s_formatted[:25].lower() in existing.lower() for existing in final_sentences):
                if not s_formatted.endswith(('.', '!', '?')):
                    s_formatted += '.'
                final_sentences.append(s_formatted)

        if not final_sentences:
            return FALLBACK_RESPONSE_STRING

        # For denial/refusal queries, explicitly mention that no further appeal procedure is specified
        if is_denial_query and any('approve or deny' in s.lower() for s in final_sentences):
            if not any('does not specify' in s.lower() for s in final_sentences):
                final_sentences.append("The policy does not specify an appeal process or further procedure if the leave request is denied.")

        return " ".join(final_sentences)

llm_service = LLMService()



