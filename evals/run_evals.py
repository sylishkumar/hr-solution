"""
Evaluation Suite Execution Engine (LLM-as-a-Judge)
Executes test cases from evals/eval_dataset.json against RootOrchestrator, scores output
using LLMJudge (Gemini 2.5 Pro), and writes structured evaluation results to evals/eval_results.json.
"""

import json
import os
import time
from typing import Dict, Any, List
from datetime import datetime
from agents.root_orchestrator import RootOrchestrator
from evals.llm_judge import LLMJudge

EVAL_DIR = os.path.dirname(__file__)
DATASET_PATH = os.path.join(EVAL_DIR, "eval_dataset.json")
RESULTS_PATH = os.path.join(EVAL_DIR, "eval_results.json")

def run_evaluations() -> Dict[str, Any]:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Evaluation dataset not found at {DATASET_PATH}. Run generate_evalset.py first.")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    orchestrator = RootOrchestrator()
    judge = LLMJudge(model_name="gemini-2.5-pro")

    total_cases = len(dataset)
    passed_cases = 0
    grounding_score_sum = 0.0
    grounding_count = 0
    security_blocked_count = 0
    hitl_gated_count = 0

    case_results: List[Dict[str, Any]] = []
    start_time = time.time()

    for tc in dataset:
        tc_id = tc["test_case_id"]
        category = tc["category"]
        prompt = tc["user_prompt"]
        emp_id = tc["employee_id"]
        expected_status = tc["expected_status"]
        expected_action = tc["expected_action"]

        # Run turn against RootOrchestrator
        res = orchestrator.process_user_turn(prompt, employee_id=emp_id)

        actual_status = res.get("status")
        actual_action = res.get("action")
        actual_response = res.get("response", "")
        grounding_score = res.get("groundingScore")

        # LLM Judge evaluation
        judge_verdict = judge.evaluate_turn(
            user_prompt=prompt,
            actual_response=str(actual_response),
            category=category,
            expected_status=expected_status,
            actual_status=actual_status,
            expected_action=expected_action,
            actual_action=actual_action
        )

        is_pass = (judge_verdict.get("verdict") == "PASS")

        if category == "Policy_QA" and grounding_score is not None:
            if tc.get("expected_grounded"):
                grounding_score_sum += grounding_score
                grounding_count += 1

        if category == "Security_Defense" and actual_status == "BLOCKED":
            security_blocked_count += 1

        if actual_status == "HITL_REQUIRED":
            hitl_gated_count += 1

        if is_pass:
            passed_cases += 1

        case_results.append({
            "test_case_id": tc_id,
            "category": category,
            "prompt": prompt,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "expected_action": expected_action,
            "actual_action": actual_action,
            "grounding_score": grounding_score,
            "llm_judge": judge_verdict,
            "passed": is_pass
        })

    duration = time.time() - start_time
    pass_rate = (passed_cases / total_cases) * 100.0 if total_cases > 0 else 0.0
    avg_grounding = (grounding_score_sum / grounding_count) if grounding_count > 0 else 1.0

    eval_submission = {
        "evaluation_metadata": {
            "eval_run_id": f"eval-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "judge_model": "gemini-2.5-pro",
            "eval_duration_seconds": round(duration, 2),
            "total_test_cases": total_cases
        },
        "summary_metrics": {
            "pass_rate_percentage": round(pass_rate, 2),
            "passed_cases": passed_cases,
            "failed_cases": total_cases - passed_cases,
            "policy_qa_avg_grounding_score": round(avg_grounding, 4),
            "security_injections_blocked": security_blocked_count,
            "hitl_confirmation_cards_generated": hitl_gated_count,
            "meets_deployment_threshold": (pass_rate >= 98.0 and avg_grounding >= 0.85)
        },
        "case_details_sample": case_results[:20]
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_submission, f, indent=2)

    print(f"\n================ EVALUATION SUMMARY ================")
    print(f"Total Test Cases: {total_cases}")
    print(f"Passed Test Cases: {passed_cases} ({pass_rate:.2f}%)")
    print(f"Policy Q&A Avg Grounding Score: {avg_grounding:.4f}")
    print(f"Security Blocks: {security_blocked_count}")
    print(f"HITL Gated Confirmations: {hitl_gated_count}")
    print(f"LLM Judge Model: gemini-2.5-pro ({case_results[0]['llm_judge']['judge_type']})")
    print(f"Deployment Threshold Met: {eval_submission['summary_metrics']['meets_deployment_threshold']}")
    print(f"Results saved to: {RESULTS_PATH}")
    print(f"====================================================")

    return eval_submission

if __name__ == "__main__":
    run_evaluations()
