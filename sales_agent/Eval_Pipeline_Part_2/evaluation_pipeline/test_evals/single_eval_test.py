import os
import json
import sys
from dotenv import load_dotenv
from openevals.llm import create_llm_as_judge
from pathlib import Path
from openevals.prompts import (
    CORRECTNESS_PROMPT,
    CONCISENESS_PROMPT,
    HALLUCINATION_PROMPT
)
from langchain_cohere import ChatCohere

# Add parent directory (evaluation_pipeline) to sys.path for imports
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from eval_prompt import CUSTOM_CRITERIA_PROMPT
load_dotenv()

class RagasTest:
    def __init__(self):
        self.cohere_judge = ChatCohere(
            model="command-a-03-2025", 
            temperature=0.0,
            cohere_api_key=os.getenv("COHERE_API_KEY")
        )

    def initialize_evaluators(self):
        self.correctness_evaluator = create_llm_as_judge(
            prompt=CORRECTNESS_PROMPT,
            judge=self.cohere_judge,
            feedback_key="correctness"
        )
        self.conciseness_evaluator = create_llm_as_judge(
            prompt=CONCISENESS_PROMPT,
            judge=self.cohere_judge,
            feedback_key="conciseness"
        )
        self.hallucination_evaluator = create_llm_as_judge(
            prompt=HALLUCINATION_PROMPT,
            judge=self.cohere_judge,
            feedback_key="hallucination"
        )
        self.criteria_evaluator = create_llm_as_judge(
            prompt=CUSTOM_CRITERIA_PROMPT,
            judge=self.cohere_judge,
            feedback_key="criteria_adherence"
        )

    def run_evaluation(self, data_point):
        print(f"--- Evaluating: {data_point['question']} ---")
        
        results = {}

        # 1. Run Correctness
        results['correctness'] = self.correctness_evaluator(
            inputs=data_point['question'],
            outputs=data_point['agent_response'],
            reference_outputs =data_point['golden_answer']
        )

        # 2. Run Conciseness
        results['conciseness'] = self.conciseness_evaluator(
            inputs=data_point['question'],
            outputs=data_point['agent_response'],
            context=data_point['golden_answer']
        )

        # 3. Run Hallucination
        # We pass golden_answer as 'context' to ensure the agent isn't making things up 
        # relative to the ground truth.
        results['hallucination'] = self.hallucination_evaluator(
            inputs=data_point['question'],
            outputs=data_point['agent_response'],
            context=data_point['golden_answer'],
            reference_outputs=""
        )

        #4. Run Custom Criteria
        results['criteria_adherence'] = self.criteria_evaluator(
            inputs=data_point['question'], 
            outputs=data_point['agent_response'],
            criteria=data_point['evaluation_criteria']
        )

        return results

# 4. Test with your Data
if __name__ == "__main__":
    # Your provided JSON data
    test_data = {
        "question": "How many customers are currently on the Enterprise plan?",
        "golden_answer": "There are 6 customers on the Enterprise plan: Acme Corp, Global Finance Ltd, Legal Partners LLP, Pharma Innovations, MegaCorp International, and City Hospital Network.",
        "evaluation_criteria": "Should correctly count all subscriptions with plan_tier='Enterprise' (6 total)",
        "agent_response": "There are currently 6 customers on the Enterprise plan."
    }
    test_data_1 = {
        "question": "What is the monthly revenue for Acme Corp?",
        "golden_answer": "Acme Corp generates $15,000 in monthly revenue.",
        "evaluation_criteria": "Should extract monthly_revenue from the Acme Corp subscription record.",
        "agent_response": "Acme Corp generates $15,000 per month."
    }
    ragas_test = RagasTest()
    ragas_test.initialize_evaluators()
    eval_results = ragas_test.run_evaluation(test_data_1)

    print("\n=== Evaluation Results ===")
    for metric, result in eval_results.items():
        print(f"\nMetric: {metric.upper()}")
        print(f"Score: {result['score']}")
        print(f"Reason: {result['comment']}")
    
    # Print custom metric (criteria_adherence) in JSON format
    print("\n" + "="*60)
    print("=== Custom Metric (criteria_adherence) JSON Format ===")
    print("="*60)
    custom_metric = eval_results.get('criteria_adherence', {})
    print(json.dumps(custom_metric, indent=2))
    print("\n=== Raw Result Type ===")
    print(f"Type: {type(custom_metric)}")
    print(f"Keys: {list(custom_metric.keys()) if isinstance(custom_metric, dict) else 'Not a dict'}")