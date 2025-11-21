import re
from typing import Optional, Tuple
from prompt import GUARDRAIL_PROMPT

class Guardrails:
    """
    Guardrailsclass that manages rejecting questions using regex and LLM.
    Multi-layered approach for detecting sensitive information requests.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Guardrails with detection methods.
        
        Args:
            llm: Optional LLM instance for LLM-based detection
        """
        self.llm = llm
        
        # Regex patterns for sensitive information detection
        self.sensitive_patterns = [
            # Credit card and payment information
            r'\bcredit\s*card\s*(number|num|#|details|info)\b',
            r'\bcard\s*number\b',
            r'\bcc\s*number\b',
            r'\bpayment\s*card\s*details?\b',
            r'\bbank\s*account\s*(number|num|#)\b',
            r'\baccount\s*number\b',
            
            # Personal identification
            r'\bssn\b',
            r'\bsocial\s*security\s*(number|num|#)\b',
            r'\bpassport\s*(number|num|#)\b',
            r'\bdriver\s*license\s*(number|num|#)\b',
            
            # Personal addresses
            r'\bhome\s*address\b',
            r'\bpersonal\s*address\b',
            r'\bresidential\s*address\b',
            r'\bmailing\s*address\b',
            
            # Bulk data extraction
            r'\ball\s*(customer|client|user)\s*(email|emails|address|addresses|contact|contacts)\b',
            r'\b(email|emails|address|addresses)\s*(list|all|every|dump)\b',
            r'\bphone\s*(number|numbers|list|all)\b',
            r'\bcontact\s*(list|all|every|dump)\b',
            
            # Other sensitive patterns
            r'\bpassword\b',
            r'\bpin\s*(number|num|#|code)\b',
            r'\bsecurity\s*code\b',
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
    
    def _check_regex(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check query against regex patterns for sensitive information.
        
        Args:
            query: User query to check
            
        Returns:
            Tuple of (should_reject, reason)
        """
        query_lower = query.lower()  # Use lowercase for consistency
        
        for pattern in self.compiled_patterns:
            if pattern.search(query_lower):  # Use query_lower instead of query
                matched_pattern = pattern.pattern
                return True, f"Query matches sensitive pattern: {matched_pattern}"
        
        return False, None
    
    def _check_llm(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Use LLM to analyze query intent for sensitive information.
        
        Args:
            query: User query to check
            
        Returns:
            Tuple of (should_reject, reason)
        """
        if not self.llm:
            return False, None
        
        try:
            guardrail_prompt = GUARDRAIL_PROMPT.format(query=query)
            response = self.llm.invoke(guardrail_prompt)
            response_text = response.content.strip().upper()
            
            if "REJECT" in response_text:
                return True, "LLM detected sensitive information request"
            return False, None
        except Exception as e:
            # If LLM check fails, don't reject (fail open)
            print(f"Warning: Guardrail LLM check failed: {e}")
            return False, None
    
    def should_reject(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a query should be rejected using multi-layered detection.
        
        Detection order:
        1. Regex-based quick check (fast, catches common patterns)
        2. LLM-based nuanced detection (slower, catches edge cases)
        
        Args:
            query: User query to check
            
        Returns:
            Tuple of (should_reject: bool, reason: Optional[str])
        """
        # Quick regex check first
        should_reject, reason = self._check_regex(query)
        if should_reject:
            return True, reason
        
        # LLM-based check for nuanced cases
        should_reject, reason = self._check_llm(query)
        if should_reject:
            return True, reason
        
        return False, None

