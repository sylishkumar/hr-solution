"""
Main entry point for interactive testing of the Enterprise HR Agentic Solution.
"""

import sys
from agents.root_orchestrator import RootOrchestrator

def main():
    orchestrator = RootOrchestrator()
    print("=========================================================")
    print(" Enterprise HR Agentic Assistant (Local Test CLI) ")
    print("=========================================================")
    print("Type your request or 'exit' to quit.\n")

    employee_id = "EMP1024"

    while True:
        try:
            prompt = input(f"[{employee_id}] > ")
            if not prompt.strip():
                continue
            if prompt.strip().lower() in ["exit", "quit"]:
                break

            result = orchestrator.process_user_turn(prompt, employee_id=employee_id)
            print("\n--- Assistant Response ---")
            print(f"Status: {result.get('status')}")
            if result.get("agent"):
                print(f"Agent: {result.get('agent')}")
            if result.get("response"):
                print(f"Response:\n{result.get('response')}")
            if result.get("status") == "HITL_REQUIRED":
                print(f"Action Proposal: {result.get('card_summary')}")
                print(f"Parameters: {result.get('parameters')}")
                confirm = input("\nDo you want to confirm & submit this action? (y/n): ")
                if confirm.strip().lower() in ["y", "yes"]:
                    conf_res = orchestrator.process_user_turn(
                        prompt,
                        employee_id=employee_id,
                        confirmation={
                            "action": result.get("action"),
                            "parameters": result.get("parameters")
                        }
                    )
                    print("\n--- Action Execution Result ---")
                    print(f"Status: {conf_res.get('status')}")
                    print(f"Response: {conf_res.get('response')}")
            print("--------------------------\n")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
