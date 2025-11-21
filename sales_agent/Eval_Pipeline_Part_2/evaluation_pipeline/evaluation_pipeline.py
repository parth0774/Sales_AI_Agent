import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from openevals.llm import create_llm_as_judge
from openevals.prompts import (
    CORRECTNESS_PROMPT,
    CONCISENESS_PROMPT,
    HALLUCINATION_PROMPT
)
from eval_prompt import CUSTOM_CRITERIA_PROMPT
from langchain_cohere import ChatCohere
load_dotenv()

class RagasTest:
    def __init__(self):
        self.cohere_judge = ChatCohere(
            model="command-a-03-2025", 
            temperature=0.0,
            cohere_api_key=os.getenv("COHERE_PROD_API_KEY")
        )

    def initialize_evaluators(self):
        self.correctness_evaluator = create_llm_as_judge(
            prompt=CORRECTNESS_PROMPT,
            judge=self.cohere_judge,
            feedback_key="correctness",
            choices=[0.0,0.5,0.8,1.0]
        )
        self.conciseness_evaluator = create_llm_as_judge(
            prompt=CONCISENESS_PROMPT,
            judge=self.cohere_judge,
            feedback_key="conciseness",
            choices=[0.0,0.5,0.8,1.0]
        )
        self.hallucination_evaluator = create_llm_as_judge(
            prompt=HALLUCINATION_PROMPT,
            judge=self.cohere_judge,
            feedback_key="hallucination",
            choices=[0.0,0.5,0.8,1.0]
        )
        self.criteria_evaluator = create_llm_as_judge(
            prompt=CUSTOM_CRITERIA_PROMPT,
            judge=self.cohere_judge,
            feedback_key="criteria_adherence",
            choices=[0.0,0.5,0.8,1.0]
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

    def evaluate_dataset(self, dataset_path: Path, output_csv_path: Path):
        """Load dataset from JSON and evaluate all data points, saving results to CSV."""
        # Load dataset
        print(f"Loading dataset from {dataset_path}...")
        with dataset_path.open("r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        data_points = dataset.get("results", [])
        if not data_points:
            raise ValueError("No 'results' found in dataset JSON")
        
        print(f"Found {len(data_points)} data points to evaluate.\n")
        
        # Initialize evaluators
        print("Initializing evaluators...")
        self.initialize_evaluators()
        print("Evaluators initialized.\n")
        
        # Prepare CSV data
        csv_rows = []
        
        # Evaluate each data point
        for idx, data_point in enumerate(data_points, start=1):
            print(f"[{idx}/{len(data_points)}] Processing: {data_point['question'][:60]}...")
            
            try:
                eval_results = self.run_evaluation(data_point)
                
                # Prepare row for CSV
                row = {
                    "question": data_point.get("question", ""),
                    "golden_answer": data_point.get("golden_answer", ""),
                    "agent_response": data_point.get("agent_response", ""),
                    "evaluation_criteria": data_point.get("evaluation_criteria", ""),
                    "correctness_score": eval_results.get("correctness", {}).get("score", ""),
                    "correctness_comment": eval_results.get("correctness", {}).get("comment", ""),
                    "conciseness_score": eval_results.get("conciseness", {}).get("score", ""),
                    "conciseness_comment": eval_results.get("conciseness", {}).get("comment", ""),
                    "hallucination_score": eval_results.get("hallucination", {}).get("score", ""),
                    "hallucination_comment": eval_results.get("hallucination", {}).get("comment", ""),
                    "criteria_adherence_score": eval_results.get("criteria_adherence", {}).get("score", ""),
                    "criteria_adherence_comment": eval_results.get("criteria_adherence", {}).get("comment", ""),
                }
                csv_rows.append(row)
                
                print(f"  ✓ Completed\n")
                
            except Exception as e:
                print(f"  ✗ Error evaluating: {str(e)}\n")
                # Add row with error
                row = {
                    "question": data_point.get("question", ""),
                    "golden_answer": data_point.get("golden_answer", ""),
                    "agent_response": data_point.get("agent_response", ""),
                    "evaluation_criteria": data_point.get("evaluation_criteria", ""),
                    "correctness_score": "",
                    "correctness_comment": f"Error: {str(e)}",
                    "conciseness_score": "",
                    "conciseness_comment": "",
                    "hallucination_score": "",
                    "hallucination_comment": "",
                    "criteria_adherence_score": "",
                    "criteria_adherence_comment": "",
                }
                csv_rows.append(row)
        
        # Write to CSV
        print(f"Writing results to {output_csv_path}...")
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        if csv_rows:
            fieldnames = csv_rows[0].keys()
            with output_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
        
        print(f"✓ Evaluation complete! Results saved to {output_csv_path}")
        print(f"  Total evaluations: {len(csv_rows)}")


if __name__ == "__main__":
    # Get current directory and file paths
    CURRENT_DIR = Path(__file__).resolve().parent
    dataset_path = CURRENT_DIR / "agent_responses" / "evaluation_dataset_v2.json"
    output_csv_path = CURRENT_DIR / "evaluation_output" / "evaluation_results_v2.csv"
    
    # Run evaluation pipeline
    ragas_test = RagasTest()
    ragas_test.evaluate_dataset(dataset_path, output_csv_path)
