# Implementation Plan: Enterprise HR Agentic Solution

Based on the Solution Design Document ([`hr_agentic_solution_sdd.md`](file:///usr/local/google/home/abhradip/hrsolution/hr_agentic_solution_sdd.md)), this plan outlines the step-by-step implementation for the **Enterprise HR Agentic Solution**, focusing on:
1. **Policy Q&A Sub-Agent & RAG Grounding Verification**
2. **HRMS Integration (`WorkWeek` MCP Server & Tools)**
3. **ITMS Integration (`ServiceImmediately` MCP Server & Tools)**
4. **Evalset Generation (Golden Evaluation Dataset)**
5. **Evaluation Suite & Eval JSON Submission / Scoring Engine**

---

## 🏗️ Proposed Project Structure

```
hrsolution/
├── hr_agentic_solution_sdd.md          # Solution Design Document
├── implementation_plan.md              # This Implementation Plan
├── config.py                           # Central configuration & environment variables
├── requirements.txt                    # Python dependencies
│
├── mock_services/                      # Mock MCP Servers & Endpoints (for local testing & evals)
│   ├── workweek_mcp_server.py          # WorkWeek HCM Mock MCP Server
│   └── service_immediately_mcp_server.py # ServiceImmediately ITSM Mock MCP Server
│
├── data/
│   └── policies/                       # HR Policy Documents (Markdown / Text)
│       ├── global_leave_policy_2026.md
│       ├── equipment_policy_2026.md
│       └── travel_expense_policy_2026.md
│
├── agents/                             # ADK Agent Mesh
│   ├── __init__.py
│   ├── root_orchestrator.py            # Gemini 3.1 Pro Root Orchestrator (Intent Routing & HITL)
│   ├── policy_qa_agent.py              # PolicyQAAgent (Gemini 3.7 Flash + Grounding)
│   ├── workweek_agent.py               # WorkWeekAgent (Gemini 3.7 Flash + WorkWeek Tools)
│   └── service_immediately_agent.py    # ServiceImmediatelyAgent (Gemini 3.7 Flash + ITSM Tools)
│
├── tools/                              # Tool Definitions & MCP Clients
│   ├── __init__.py
│   ├── policy_search_tool.py           # Local Policy Hybrid Search & Grounding Tool
│   ├── workweek_tools.py               # WorkWeek MCP Tools (Balances, PTO, Profile, Address)
│   └── service_immediately_tools.py    # ServiceImmediately MCP Tools (Tickets, Comments, Status)
│
├── evals/                              # Evaluation Framework & Flywheel
│   ├── __init__.py
│   ├── generate_evalset.py             # Evalset Generator (Produces 500+ golden test cases)
│   ├── eval_dataset.json               # Generated Golden Evalset
│   ├── run_evals.py                    # Evaluation Execution Engine (LLM-as-a-Judge)
│   └── eval_results.json               # Output Evaluation Benchmark JSON
│
└── main.py                             # Interactive CLI / System Entry Point
```

---

## 📋 Implementation Steps

### Step 1: Configuration & Workspace Setup
- Define `requirements.txt` with required dependencies (`google-genai`, `fastmcp`, `pydantic`, `httpx`, `asyncio`, etc.).
- Create `config.py` for model selections (`gemini-3.1-pro` for orchestrator/judge, `gemini-3.7-flash` for sub-agents), endpoints, and grounding thresholds (`groundingScore >= 0.85`).
- Create initial policy handbook files in `data/policies/` covering leave, equipment procurement, and travel policies with page/section anchors.

### Step 2: HRMS & ITMS Mock MCP Services
- Implement `mock_services/workweek_mcp_server.py` exposing FastMCP endpoints for WorkWeek HCM:
  - `get_current_employee_id`, `get_employee_balances`, `request_time_off`, `update_personal_info`, `get_personal_info`, `get_leave_requests`, `cancel_leave_request`.
- Implement `mock_services/service_immediately_mcp_server.py` exposing FastMCP endpoints for ServiceImmediately ITSM:
  - `list_tickets`, `create_ticket`, `add_ticket_comment`, `update_ticket_status`.

### Step 3: Tool Integrations & Policy Grounding Engine
- Implement `tools/policy_search_tool.py`:
  - Dense + keyword hybrid retrieval over `data/policies/`.
  - Calculates attribution mappings (`groundingSupports`) and confidence score (`groundingScore`).
  - Enforces refusal gate if `groundingScore < 0.85`.
- Implement `tools/workweek_tools.py` and `tools/service_immediately_tools.py` wrapping FastMCP client calls.

### Step 4: ADK Multi-Agent Mesh & Orchestrator
- Implement `agents/policy_qa_agent.py`: Read-only Policy Q&A sub-agent using `Gemini 3.7 Flash`.
- Implement `agents/workweek_agent.py`: WorkWeek HCM sub-agent handling balances, PTO, and profile changes.
- Implement `agents/service_immediately_agent.py`: ITSM sub-agent handling hardware and IT service tickets.
- Implement `agents/root_orchestrator.py`: Root Orchestrator using `Gemini 3.1 Pro`:
  - Classifies user turn intent and routes to sub-agents.
  - Generates Human-in-the-Loop (HITL) Action Confirmation Cards for state-mutating tools (`request_time_off`, `update_personal_info`, `create_ticket`).
  - Orchestrates sequential multi-step sagas (e.g. Equipment Procurement: Policy lookup $\rightarrow$ Profile check $\rightarrow$ HITL Confirmation $\rightarrow$ ITSM Ticket).

### Step 5: Evalset Generation Engine (`evals/generate_evalset.py`)
- Build a script to generate a 500+ sample evaluation dataset (`evals/eval_dataset.json`):
  1. **Policy Q&A**: Valid policy questions, unanswerable/out-of-scope questions, edge cases.
  2. **HRMS WorkWeek**: Balance inquiries, time-off requests, personal info updates, cancellations, insufficient balance scenarios.
  3. **ITMS ServiceImmediately**: Ticket listings, creation, comments, status updates.
  4. **Multi-Step Cross-Domain Sagas**: Combined policy checking + profile verification + ticket submission.
  5. **Security & Prompt Injections**: Direct prompt injections, adversarial overrides, unauthorized employee ID access attempts.
  6. **HITL Confirmation Compliance**: Verifying mutating actions correctly return a pending HITL confirmation payload.

### Step 6: Evaluation Suite & Eval JSON Submission Engine (`evals/run_evals.py`)
- Implement an evaluation runner using `Gemini 3.1 Pro` as LLM-as-a-Judge:
  - Iterates over `evals/eval_dataset.json` and executes each turn against the agent mesh.
  - Scores each response on:
    - **Intent Routing Accuracy**
    - **Tool Calling Schema Precision & Parameter Extraction**
    - **Grounding Faithfulness & Citation Validity**
    - **HITL Gate Enforcement**
    - **Security Injection Resistance**
  - Outputs a comprehensive evaluation report in JSON format (`evals/eval_results.json`).

### Step 7: Local Evaluation Run & Verification
- Execute `python evals/generate_evalset.py` to create `eval_dataset.json`.
- Execute `python evals/run_evals.py` to evaluate the agent implementation offline.
- Inspect `evals/eval_results.json` to confirm all test cases pass target thresholds before running on server.

---

## 📊 Summary of Focus Areas
| Focus Area | Key Features & Deliverables |
| :--- | :--- |
| **Policy Q&A** | Hybrid dense/keyword search, sentence attributions (`groundingSupports`), refusal gate when `groundingScore < 0.85`. |
| **HRMS Integration** | WorkWeek FastMCP server & tools: balances, PTO requests, profile updates, leave cancellation. |
| **ITMS Integration** | ServiceImmediately FastMCP server & tools: ticket listing, ticket creation, status updates, comment threads. |
| **Evalset Generation** | Programmatic generator for 500+ golden test cases covering all 5 core domains & security injections. |
| **Eval JSON Submission** | Offline LLM-as-a-Judge scoring pipeline generating structured `eval_results.json` before server deployment. |

---
*Please review this implementation plan. Upon your approval, we will begin execution step-by-step starting with Step 1.*
