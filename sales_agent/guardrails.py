import re

class Guardrails:
    def __init__(self, llm):
        self.llm = llm

        # List of sensitive regex patterns
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
            r'\bsecurity\s*code\b'
        ]

        # Compile patterns for performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns
        ]

    def _check_regex(self, text: str):
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True, f"Matched sensitive pattern: {pattern.pattern}"
        return False, "No sensitive pattern detected"

    def should_reject(self, text: str):
        # Step 1: Regex first
        regex_flagged, reason = self._check_regex(text)
        if regex_flagged:
            return True, f"Regex Reject — {reason}"

        # Step 2: LLM evaluation if regex allows it
        llm_prompt = f"""
        You are a safety classifier. Determine whether the following text asks for
        sensitive or protected personal information.

        Text: "{text}"

        Respond ONLY with:
        - "ALLOW"
        - "REJECT"
        """

        llm_response = self.llm.invoke(llm_prompt).content.strip().upper()

        if llm_response == "REJECT":
            return True, "LLM Reject — considered sensitive"

        return False, "LLM Allow — safe"
