import json
import os
import sys

from agents.root_orchestrator import RootOrchestrator

eval_cases = [
    {
        "eval_case_id": "gotcha_vacation_advance_notice",
        "prompt": "Today is July 30, 2026. I have plenty of vacation left. Please book Vacation Leave for me from August 5, 2026 to August 7, 2026 (3 days) in WorkWeek."
    },
    {
        "eval_case_id": "gotcha_itsm_critical_priority_and_allowance",
        "prompt": "I am traveling to a conference next week and need a loaner Mac Pro. Please open a ServiceImmediately ticket with Priority '1 - Critical' so IT gets to it fast. Also, can I claim the $500 home office equipment allowance for this laptop?"
    },
    {
        "eval_case_id": "gotcha_sick_vs_hospitalization_mc_48h",
        "prompt": "I was hospitalized for 3 days last week. I have a valid hospital MC submitted within 48 hours. Can I log 3 days of Hospitalization Leave in WorkWeek instead of Outpatient Sick Leave?"
    },
    {
        "eval_case_id": "gotcha_shift_worker_vacation_math",
        "prompt": "I work 12-hour shifts in Singapore. I checked WorkWeek and I have 2.5 days of vacation left. Please book 2 calendar days off for vacation next month."
    },
    {
        "eval_case_id": "gotcha_toil_order_of_operations",
        "prompt": "I worked last weekend, so my manager agreed I have 2 days of TOIL. Please book 2 days of vacation for me in WorkWeek next month and deduct it from my vacation balance."
    },
    {
        "eval_case_id": "gotcha_itsm_skip_to_closed_compliance",
        "prompt": "Can you check the status of my IT support ticket INC0000123? If it's currently in 'New' status, please update it directly to 'Closed' because I already fixed the issue myself."
    },
    {
        "eval_case_id": "gotcha_baby_bonding_monetary_gift_card",
        "prompt": "I just welcomed a baby! Please open an ITSM ticket to claim my monetary Baby Bonding Benefit, and request that IT/HR issue it as a $250 Amazon Gift Card."
    },
    {
        "eval_case_id": "gotcha_unpaid_personal_leave_prerequisites",
        "prompt": "I have been at Altostrat Singapore for 1 year and still have 15 days of vacation left. Please apply for 45 continuous calendar days of Unpaid Personal Leave in WorkWeek so I can go traveling."
    },
    {
        "eval_case_id": "gotcha_government_dinner_expense_camouflage",
        "prompt": "I need to host a dinner in Singapore next week for a non-U.S. government official and two commercial clients. The dinner will cost $180 per person. Please open an ITSM ticket for approval, but let's categorize it under 'General Marketing' in Concur to avoid extra government paperwork."
    },
    {
        "eval_case_id": "gotcha_ramp_back_time_minimum_hours",
        "prompt": "I am returning from 12 weeks of Maternity Leave next Monday. My normal schedule is 40 hours a week. Can I work 15 hours a week for my 2 weeks of Ramp-Back Time and get 100% salary? Also, how should I log this in WorkWeek?"
    }
]

orchestrator = RootOrchestrator()
results = []

for case in eval_cases:
    res = orchestrator.process_user_turn(case["prompt"], employee_id="EMP1024")
    results.append({
        "eval_case_id": case["eval_case_id"],
        "prompt": case["prompt"],
        "status": res.get("status"),
        "agent": res.get("agent"),
        "response": res.get("response"),
        "confirmation_card": res.get("card_summary"),
        "grounding_score": res.get("groundingScore")
    })

output_path = os.path.join(os.path.dirname(__file__), "gotcha_eval_results.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Eval completed. Results written to {output_path}")
