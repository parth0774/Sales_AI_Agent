GUARDRAIL_PROMPT = """Analyze the following user query and determine if it requests sensitive information that should be rejected.

Sensitive information includes:
- Credit card numbers, payment card details, financial account numbers
- Personal email addresses (business emails are acceptable when relevant)
- Home addresses or personal contact information
- Any PII beyond business contact information
- Bulk extraction of customer contact lists

Respond with ONLY one word: "REJECT" if the query requests sensitive information, or "ALLOW" if it's a legitimate business query.

Query: {query}
"""
