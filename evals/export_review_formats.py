"""
Golden Set Review Exporter
Reads evals/eval_dataset.json and generates clean Markdown and CSV review files
for manual inspection.
"""

import json
import os
import csv
from typing import List, Dict, Any

EVAL_DIR = os.path.dirname(__file__)
DATASET_PATH = os.path.join(EVAL_DIR, "eval_dataset.json")
MD_PATH = os.path.join(EVAL_DIR, "golden_evalset_review.md")
CSV_PATH = os.path.join(EVAL_DIR, "golden_evalset_review.csv")

def export_review_files():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset file not found at {DATASET_PATH}")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    # 1. Export CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Test Case ID", "Category", "Target Agent",
            "User Prompt", "Expected Status", "Expected Action", "Employee ID"
        ])
        for tc in dataset:
            writer.writerow([
                tc.get("test_case_id"),
                tc.get("category"),
                tc.get("target_agent"),
                tc.get("user_prompt"),
                tc.get("expected_status"),
                tc.get("expected_action") or "N/A",
                tc.get("employee_id")
            ])

    # 2. Export Markdown
    categories = {}
    for tc in dataset:
        cat = tc.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tc)

    md_lines = [
        "# Golden Evaluation Dataset Manual Review Document",
        f"\n**Total Test Cases**: {len(dataset)}",
        f"**Generated Date**: {os.path.basename(DATASET_PATH)}",
        "\nThis document contains the complete benchmark dataset used for evaluating the Enterprise HR Agentic Solution.\n",
        "## Category Breakdown\n"
    ]

    for cat, items in categories.items():
        md_lines.append(f"- **{cat}**: {len(items)} test cases")

    md_lines.append("\n---\n")

    for cat, items in categories.items():
        md_lines.append(f"## Category: {cat} ({len(items)} cases)\n")
        md_lines.append("| ID | Prompt | Expected Status | Expected Action | Target Agent |")
        md_lines.append("|---|---|---|---|---|")
        for tc in items:
            prompt_esc = tc["user_prompt"].replace("|", "\\|")
            act = tc.get("expected_action") or "N/A"
            target_ag = tc.get("target_agent", "Orchestrator")
            md_lines.append(f"| `{tc['test_case_id']}` | {prompt_esc} | `{tc['expected_status']}` | `{act}` | `{target_ag}` |")
        md_lines.append("\n")

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Exported {len(dataset)} test cases to:")
    print(f" - Markdown: {MD_PATH}")
    print(f" - CSV: {CSV_PATH}")

if __name__ == "__main__":
    export_review_files()
