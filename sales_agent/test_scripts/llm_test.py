import os
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")

# Initialize LLM
llm = ChatCohere(
    model="command-a-03-2025",
    cohere_api_key=api_key,
    temperature=0.3
)

print("Test 1: Simple prompt")
response = llm.invoke("What is Python?")
print(response.content)
print("\n")
print("Test 2: Sales question")
response = llm.invoke("Give me 3 benefits of cloud computing in sales")
print(response.content)
