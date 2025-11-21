from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
from langchain_cohere import ChatCohere
import os
from dotenv import load_dotenv
load_dotenv()

# 1. Define your Cohere judge
cohere_judge = ChatCohere(
    model="command-a-03-2025", 
    temperature=0,
    cohere_api_key=os.getenv("COHERE_API_KEY")
)

# 2. Create the evaluator
cohere_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    judge=cohere_judge
)

# 3. Run an evaluation
result = cohere_evaluator(
    inputs="What is the capital of France?",
    outputs="The capital of France is Paris.",
    reference_outputs="Paris"
)

print(result)