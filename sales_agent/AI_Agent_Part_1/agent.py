import os
import sys
from typing import Optional
from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage
from prompt import SYSTEM_PROMPT
from guardrails import Guardrails
from tools import get_subscription_tool, create_dataframe_preamble, get_dataframe_info
from langchain.agents import create_agent
from dotenv import load_dotenv
import logging
from pathlib import Path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# Load environment variables
load_dotenv()

#Setup logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[logging.StreamHandler()]
# )

class SalesSupportAgent:
    """Sales Support Agent for subscription data queries using LangChain create_agent."""
    
    def __init__(self, csv_path: str, api_key: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            csv_path: Path to the subscription data CSV file
            api_key: Cohere API key. If not provided, will try to get from COHERE_API_KEY env var.
        """
        # Get API key
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Cohere API key not found. Please set COHERE_API_KEY environment variable "
                "or pass it as a parameter."
            )
        
        # Initialize Cohere LLM with command-a-03-2025 model
        self.llm = ChatCohere(
            model="command-a-03-2025",
            cohere_api_key=self.api_key,
            temperature=0.1,
        )
        
        
        # Initialize guardrails with LLM
        self.guardrails = Guardrails(self.llm)
        
        # Get DataFrame information once - reuse for all purposes
        df_info = get_dataframe_info(csv_path)
        
        # Get PythonREPL tool for querying subscription data
        self.tools = [get_subscription_tool(csv_path)]
        
        # Create DataFrame preamble with schema information (reusing df_info)
        df_preamble = create_dataframe_preamble(df_info)
        
        # Combine system prompt with DataFrame preamble
        enhanced_prompt = SYSTEM_PROMPT + "\n\n" + df_preamble

        self.agent = create_agent(model = self.llm, tools = self.tools, system_prompt = enhanced_prompt)

    
    def query(self, user_query: str) -> str:
        """
        Process a user query and return a response.
        
        Args:
            user_query: The user's question or request
            
        Returns:
            Agent's response as a string
        """
        # Check guardrails first
        should_reject, reason = self.guardrails.should_reject(user_query)
        
        if should_reject:
            return (
                f"I cannot fulfill this request. {reason}. "
                "I can only provide business metrics and non-sensitive subscription information. "
                "If you need sensitive information, please contact the appropriate department. "
                "However, I can help you with business-related questions about subscriptions, "
                "revenue metrics, renewals, and usage statistics."
            )
        
        # Handle empty queries
        if not user_query or not user_query.strip():
            return (
                "I'm here to help you with questions about subscription data. "
                "Please ask me something like:\n"
                "- Which enterprise customers are up for renewal?\n"
                "- What's our total MRR from Healthcare companies?\n"
                "- Show me companies with low seat utilization"
            )
        
        # Process the query through the agent
        try:
            user_query ={"messages": [HumanMessage(content=user_query)]}
            response = self.agent.invoke(input=user_query)
            return response['messages'][-1].content
        except Exception as e:
            # Handle edge cases and errors gracefully
            error_msg = str(e)
            if "parsing" in error_msg.lower() or "tool" in error_msg.lower():
                return (
                    "I encountered an issue processing your query. Could you please rephrase it? "
                    "For example, you could ask about:\n"
                    "- Subscription renewals and status\n"
                    "- Revenue metrics (MRR, ARR) by industry or plan tier\n"
                    "- Seat utilization and usage statistics\n"
                    "- Company subscription details"
                )
            else:
                return (
                    f"I encountered an error: {error_msg}. "
                    "Please try rephrasing your question or contact support if the issue persists."
                )


def main():
    """Main function for interactive testing."""
    csv_path = PROJECT_ROOT / "data" / "subscription_data.csv"
    
    print("Initializing Sales Support Agent...")
    try:
        agent = SalesSupportAgent(csv_path=csv_path)
        print("Agent initialized successfully!\n")
        print("You can now ask questions about subscription data.")
        print("Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\nAgent: ", end="")
            response = agent.query(user_input)
            print(response)
            
    except KeyboardInterrupt:
        print("\n\nSession interrupted. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

