CUSTOM_CRITERIA_PROMPT = """
You are an expert evaluator. 
Check if the system's response satisfies the specific evaluation criteria provided below.

Evaluation Criteria:
{criteria}

System Response:
{outputs}

Return a score of 1 (True) if the response fully meets the criteria, or 0 (False) otherwise.
Provide a brief reason for your decision.
"""