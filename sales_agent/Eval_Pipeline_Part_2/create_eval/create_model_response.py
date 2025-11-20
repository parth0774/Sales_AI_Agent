"""
For Evaluation of the Agent, first we need to get the response from the agent for each question in the evaluation data.
We will create new JSON file with the question, the golden answer, evaluation criteria and the response from the agent.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()

# Ensure the project root (parent of this file's directory) is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from AI_Agent_Part_1.agent import SalesSupportAgent 



def load_evaluation_data(path: Path) -> List[Dict[str, Any]]:
    """Load evaluation questions and metadata."""
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    data = payload.get("data", [])
    if not isinstance(data, list):
        raise ValueError("Evaluation file malformed: 'data' must be a list.")
    return data


def write_results(path: Path, results: List[Dict[str, str]]) -> None:
    """Persist agent responses and metadata to disk."""
    output_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)


def run_evaluation(
    evaluation_json: Path,
    subscription_csv: Path,
    output_json: Path,
) -> None:
    """Pass evaluation questions to the agent and store the responses."""
    print(f"Loading evaluation data from {evaluation_json} ...")
    evaluation_data = load_evaluation_data(evaluation_json)

    print("Initializing Sales Support Agent...")
    agent = SalesSupportAgent(csv_path=str(subscription_csv),api_key=os.getenv("COHERE_PROD_API_KEY"))
    print("Agent initialized. Processing questions...\n")

    results: List[Dict[str, str]] = []
    for idx, entry in enumerate(evaluation_data, start=1):
        question = entry.get("question", "").strip()
        if not question:
            print(f"Skipping entry #{idx}: missing question.")
            continue

        print(f"[{idx}/{len(evaluation_data)}] Question: {question}")
        response = agent.query(question)
        print(f"Response: {response}\n")

        results.append(
            {
                "question": question,
                "golden_answer": entry.get("golden_answer", ""),
                "evaluation_criteria": entry.get("evaluation_criteria", ""),
                "agent_response": response,
            }
        )

    print(f"Writing results to {output_json} ...")
    write_results(output_json, results)
    print("Evaluation complete.")


if __name__ == "__main__":
    evaluation_path = PROJECT_ROOT / "data" / "evaluation_data (1).json"
    subscription_data_path = PROJECT_ROOT / "data" / "subscription_data.csv"
    output_path = CURRENT_DIR / "agent_responses.json"

    run_evaluation(
        evaluation_json=evaluation_path,
        subscription_csv=subscription_data_path,
        output_json=output_path,
    )
