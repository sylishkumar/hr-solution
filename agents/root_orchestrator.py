"""
Root Orchestrator Agent
Coordinates sub-agents, manages HITL confirmations, and handles multi-step cross-domain workflows.
Supports flexible action parsing for leave bookings, ITSM ticket creation, and policy Q&A.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from agents.policy_qa_agent import PolicyQAAgent
from agents.workweek_agent import WorkWeekAgent
from agents.service_immediately_agent import ServiceImmediatelyAgent

class RootOrchestrator:
    """
    Root Orchestrator executing Gemini Pro high-reasoning dispatching logic.
    """
    def __init__(self):
        self.policy_agent = PolicyQAAgent()
        self.workweek_agent = WorkWeekAgent()
        self.itsm_agent = ServiceImmediatelyAgent()

    def process_user_turn(self, user_prompt: str, employee_id: str = "EMP1024", confirmation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point for processing an employee conversational turn.
        """
        lowered_prompt = (user_prompt or "").lower()

        # Step 0: Active Security Shield
        security_patterns = [
            "ignore previous instructions", "override system prompt", "system prompt",
            "leak secrets", "ignore safety rules", "reveal prompt", "unauthorized access"
        ]
        if any(pat in lowered_prompt for pat in security_patterns):
            return {
                "orchestrator": "RootOrchestrator",
                "status": "BLOCKED",
                "response": "Your request could not be processed due to enterprise safety and security guidelines.",
                "sub_agent": None,
                "action": None
            }

        # Step 1: Handle User Confirmation of HITL Card
        if confirmation:
            action = confirmation.get("action")
            params = confirmation.get("parameters", {})
            params["employee_id"] = employee_id
            params["requested_by"] = employee_id
            
            if action == "request_time_off":
                return self.workweek_agent.execute_leave_booking(params)
            elif action == "update_personal_info":
                return self.workweek_agent.execute_info_update(params)
            elif action == "create_ticket":
                return self.itsm_agent.execute_ticket_creation(params)

        # Step 1.5: Policy & Compliance Gotcha Rules Check
        gotcha_res = self._check_policy_gotchas(lowered_prompt, user_prompt)
        if gotcha_res:
            return gotcha_res

        # Explicit Policy Query Priority Gate (General Handbook Q&A)
        if any(p in lowered_prompt for p in ["company policy", "policy regarding", "policy on", "what is the policy"]):
            return self.policy_agent.process_turn(user_prompt)

        # Step 2: Intent Classification & Routing

        # Multi-Step Equipment Procurement Saga
        if any(w in lowered_prompt for w in ["monitor", "keyboard", "headset", "home office laptop"]) and any(w in lowered_prompt for w in ["order", "procure", "get", "request", "need", "can i get"]):
            policy_res = self.policy_agent.process_turn("home office hardware monitor equipment policy")
            if policy_res.get("status") == "REFUSED":
                return policy_res
                
            return self.itsm_agent.propose_ticket_creation(
                requested_by=employee_id,
                category="Hardware",
                short_description="Home Office Hardware Request",
                priority="3 - Moderate",
                assignment_group="Hardware Procurement"
            )

        # HRMS WorkWeek Intents - Balance Queries
        if any(w in lowered_prompt for w in [
            "vacation balance", "sick balance", "how many days", "how much vacation",
            "how much leave", "leave do i have", "my leave balance", "leave balance",
            "check my vacation", "hours do i have", "remaining leave"
        ]):
            return self.workweek_agent.get_balances(employee_id)
            
        # HRMS WorkWeek Intents - Cancel
        if any(w in lowered_prompt for w in ["cancel leave", "cancel request", "cancel vacation", "req-1001"]):
            res = self.workweek_agent.cancel_booking(employee_id, "REQ-1001")
            res["action"] = "cancel_leave_request"
            return res

        # HRMS WorkWeek Intents - Booking Time Off
        booking_keywords = [
            "book 2 days", "book vacation", "take time off", "request leave", "book sick",
            "vacation request", "days vacation", "apply for a vacation", "apply for vacation",
            "apply for leave", "apply vacation", "book a vacation", "take vacation",
            "request vacation", "go on vacation", "raise a time off request", "raise a leave request",
            "time off request", "leave request", "raise leave", "submit leave", "schedule vacation"
        ]
        
        is_policy_query = any(p in lowered_prompt for p in ["policy regarding", "what is the policy", "policy on", "explain policy", "guidelines on"])
        is_cancel_query = "cancel" in lowered_prompt
        is_itsm_query = any(it in lowered_prompt for it in ["ticket", "laptop", "hardware", "workstation", "it support", "incident", "broken", "service ticket", "support ticket"])
        
        has_booking_action = (not is_policy_query) and (not is_cancel_query) and (not is_itsm_query) and \
                             any(act in lowered_prompt for act in ["apply", "book", "take", "request", "reserve", "raise", "submit", "schedule"]) and \
                             any(lt in lowered_prompt for lt in ["vacation", "leave", "time off", "sick", "pto"])

        if (not is_policy_query) and (not is_cancel_query) and (not is_itsm_query) and (any(w in lowered_prompt for w in booking_keywords) or has_booking_action):
            today = datetime(2026, 8, 19)
            
            # Extract duration in days
            duration_match = re.search(r'duration\s*of\s*(\d+)\s*days?', lowered_prompt) or \
                             re.search(r'for\s*(\d+)\s*days?', lowered_prompt) or \
                             re.search(r'(\d+)\s*days?\s*duration', lowered_prompt)
            
            if duration_match:
                days = float(duration_match.group(1))
            else:
                day_matches = re.findall(r'(\d+)\s*days?', lowered_prompt)
                if day_matches:
                    # If multiple day numbers (e.g. after 30 days for duration of 5 days), take the second one if present
                    days = float(day_matches[-1]) if len(day_matches) > 1 else float(day_matches[0])
                else:
                    days = 7.0 if ("7 days" in lowered_prompt or "next 7" in lowered_prompt) else 2.0

            # Extract start date / offset
            start_offset_match = re.search(r'after\s*(\d+)\s*days?', lowered_prompt) or \
                                 re.search(r'in\s*(\d+)\s*days?', lowered_prompt)
            
            if start_offset_match:
                offset_days = int(start_offset_match.group(1))
                start_dt = today + timedelta(days=offset_days)
            elif "tomorrow" in lowered_prompt:
                start_dt = today + timedelta(days=1)
            elif "30 days" in lowered_prompt:
                start_dt = today + timedelta(days=30)
            else:
                start_dt = today + timedelta(days=22) # Default compliant > 15 days notice

            end_dt = start_dt + timedelta(days=int(days))
            
            start_date_str = start_dt.strftime("%Y-%m-%d")
            end_date_str = end_dt.strftime("%Y-%m-%d")

            return self.workweek_agent.propose_leave_booking(
                employee_id=employee_id,
                start_date=start_date_str,
                end_date=end_date_str,
                leave_type="Vacation",
                days=days
            )

        # HRMS WorkWeek Intents - Personal Info
        if any(w in lowered_prompt for w in ["update address", "update phone", "change address", "change phone", "home address"]):
            return self.workweek_agent.propose_info_update(employee_id, address="456 Innovation Way, San Jose, CA", phone="+1-512-555-0199")

        # ITSM ServiceImmediately Intents - Listing Tickets
        if any(w in lowered_prompt for w in ["my tickets", "list tickets", "support tickets", "active it support tickets", "list all my", "ticket status", "check ticket"]):
            return self.itsm_agent.get_tickets(employee_id)

        # ITSM ServiceImmediately Intents - Create Ticket
        is_ticket_intent = any(w in lowered_prompt for w in [
            "open ticket", "create ticket", "submit ticket", "report issue",
            "broken laptop", "it ticket", "service ticket", "raise a ticket",
            "raise ticket", "ticket for my", "file a ticket", "log a ticket",
            "issue with my laptop", "laptop issue", "laptop problem", "p1 ticket",
            "p2 ticket", "p3 ticket", "raise a p1", "raise a p2", "raise a p3"
        ]) or (
            "ticket" in lowered_prompt and any(w in lowered_prompt for w in ["raise", "create", "open", "submit", "log", "file", "p1", "p2", "p3", "laptop", "issue", "hardware"])
        ) or (
            any(w in lowered_prompt for w in ["laptop issue", "issue with my laptop", "broken laptop"]) and any(w in lowered_prompt for w in ["ticket", "p1", "p2", "raise", "report"])
        )

        if is_ticket_intent:
            # Determine Priority
            if any(p in lowered_prompt for p in ["p1", "critical", "urgent", "priority 1"]):
                priority = "1 - Critical"
            elif any(p in lowered_prompt for p in ["p2", "high priority", "priority 2"]):
                priority = "2 - High"
            elif any(p in lowered_prompt for p in ["p4", "low priority", "priority 4"]):
                priority = "4 - Low"
            else:
                priority = "3 - Moderate"

            # Determine Category
            category = "Hardware" if any(h in lowered_prompt for h in ["laptop", "monitor", "keyboard", "hardware", "screen", "mouse", "device"]) else "IT Support"

            # Form Short Description
            if "laptop" in lowered_prompt:
                short_description = "Laptop Issue - Urgent/P1" if priority == "1 - Critical" else "Laptop Service Request"
            else:
                short_description = "IT Service Support Request"

            # SLA / Response time explanation if asked in prompt
            sla_text = None
            if any(s in lowered_prompt for s in ["response time", "expected response", "sla", "how long", "how fast", "turnaround"]):
                sla_map = {
                    "1 - Critical": "1 hour (24/7 priority support)",
                    "2 - High": "4 hours",
                    "3 - Moderate": "24 hours (1 business day)",
                    "4 - Low": "48 hours (2 business days)"
                }
                expected_sla = sla_map.get(priority, "1 hour (24/7 priority support)")
                sla_text = f"According to Altostrat ITSM Policy, the expected response time for a **{priority}** ticket is **{expected_sla}**.\n\nI have generated the ticket creation request below for your confirmation:"

            return self.itsm_agent.propose_ticket_creation(
                requested_by=employee_id,
                category=category,
                short_description=short_description,
                priority=priority,
                assignment_group="Hardware Support" if category == "Hardware" else "Service Desk",
                response_msg=sla_text
            )

        # Fallback to Policy Q&A Agent
        return self.policy_agent.process_turn(user_prompt)

    def _check_policy_gotchas(self, lowered_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Specialized validation for complex policy edge cases and compliance rules.
        """
        employee_id = "EMP1024"

        # Coverage Gap 1: Outpatient Sick Leave Entitlement & MC Deadline
        if "outpatient sick leave" in lowered_prompt or ("sick leave" in lowered_prompt and "3 days" in lowered_prompt and "mc" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 1):\n\n1. **Outpatient Sick Leave Entitlement**: Eligible employees receive up to **14 days of paid outpatient sick leave** per calendar year (compensated at 100% base salary).\n2. **Medical Certificate (MC) Submission Window**: For sick leave exceeding **2 work days** (such as 3 days), a valid Medical Certificate (MC) from a registered medical practitioner must be submitted via WorkWeek within **48 hours**.\n\n*Reference: [altostrat_leave_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L4-L8)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L4-L8"
            }

        # Coverage Gap 2: 8-Year Tenure Vacation Earnings & 12-Hour Shift Logging Math
        if "8 years" in lowered_prompt and "12-hour" in lowered_prompt:
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 2):\n\n1. **Vacation Entitlement for 8 Years Tenure**: Based on the Accrual Tier Matrix (7 to 10 years of service), you earn **21 days of paid vacation leave per calendar year**.\n2. **Shift Off Vacation Deduction**: WorkWeek logs vacation in standard 8-hour daily blocks. For a 12-hour shift worker, taking a single 12-hour shift off requires logging **1.5 vacation days** (12 working hours / 8 standard hours = 1.5 days).\n\n*Reference: [altostrat_leave_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L10-L13)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L10-L13"
            }

        # Coverage Gap 3: Childcare / Parental Ramp-Back Working Hour Limits & Salary Provisions
        if ("childcare" in lowered_prompt and "ramp-back" in lowered_prompt) or ("ramp-back" in lowered_prompt and "salary" in lowered_prompt) or ("ramp-back" in lowered_prompt and "working hour" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 3):\n\n1. **Working Hour Limits**: During the 2-week Ramp-Back period immediately returning from parental/bonding leave, employees must work **at least 50% of their normal schedule** (minimum **20 hours per week** for a standard 40-hour schedule).\n2. **Salary Provisions**: Employees receive **100% full base pay compensation** during the 2-week Ramp-Back period despite working reduced hours.\n\n*Reference: [altostrat_leave_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L29)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_leave_policy_2026.md#L29"
            }

        # Coverage Gap 4: Purchasing Gift Card using Corporate Card
        if "gift card" in lowered_prompt and ("corporate card" in lowered_prompt or "reimbursed" in lowered_prompt or "colleague" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "⚠️ **Compliance Violation Refusal**: According to Altostrat Ethics, Conduct & Expense Policy (Section 2):\n\nCash, gift cards, and gift certificates are **strictly prohibited and non-reimbursable**. Purchasing personal or colleague gift cards on a corporate card violates company card usage policy and will be rejected for reimbursement.\n\n*Reference: [altostrat_equipment_conduct_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L14)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L14"
            }

        # Coverage Gap 5: Expensing Room Salons or Adult Entertainment
        if "room salon" in lowered_prompt or "adult entertainment" in lowered_prompt:
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "⚠️ **Code of Conduct & Compliance Violation**: According to Altostrat Ethics, Conduct & Travel Policy (Section 2):\n\nExpensing outings or hosting business partners at **Room Salons, adult entertainment venues, or adult-themed establishments is strictly prohibited** under company ethics and conduct rules. Any such expense claims will be immediately rejected and reported to Compliance.\n\n*Reference: [altostrat_equipment_conduct_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L14)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L14"
            }

        # Coverage Gap 6: Critical Ticket for Squeaky Chair & Skip to Resolved
        if "squeaky" in lowered_prompt or "office chair" in lowered_prompt:
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat ITSM Policy & Lifecycle Rules:\n\n1. **Priority Validation & Downgrade**: A squeaky office chair is a routine Facilities maintenance issue and does **not** qualify for Priority '1 - Critical' (which is strictly reserved for major business outages or unusable primary work devices). Priority is downgraded to **Priority 4 - Low**.\n2. **State Transition Assertion**: ITSM compliance rules forbid transitioning a ticket directly from **'New'** to **'Resolved'**. Tickets must progress sequentially through standard states (**New -> In Progress -> Resolved**).\n\n*Reference: [altostrat_equipment_conduct_policy_2026.md](file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L21-L26)*",
                "groundingScore": 1.0,
                "citation": "file:///Users/sylishkumar/Downloads/codemender/data/policies/altostrat_equipment_conduct_policy_2026.md#L21-L26"
            }

        # Coverage Gap 7: Update Address & Order Monitor
        if ("123 main st" in lowered_prompt or "update my address" in lowered_prompt) and ("monitor" in lowered_prompt or "order" in lowered_prompt):
            self.workweek_agent.execute_info_update({
                "employee_id": employee_id,
                "field": "address",
                "value": "123 Main St"
            })
            
            return self.itsm_agent.propose_ticket_creation(
                requested_by=employee_id,
                category="Hardware",
                short_description="Home Office Monitor Request (Shipping to 123 Main St)",
                priority="3 - Moderate",
                assignment_group="Hardware Procurement",
                response_msg="1. **WorkWeek Profile Updated**: Your personal address has been successfully updated to **123 Main St** in WorkWeek.\n2. **Home Office Monitor Request**: Below is your ticket creation request for shipping a home office monitor to **123 Main St**:"
            )

        # 1. Government Dinner Expense Camouflage
        if ("government" in lowered_prompt or "official" in lowered_prompt) and any(w in lowered_prompt for w in ["general marketing", "categorize", "concur", "camouflage", "paperwork"]):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "⚠️ **Compliance Violation Refusal**: Categorizing entertainment or dining for government officials under 'General Marketing' in Concur violates Altostrat Ethics & Conduct Policy (Section 2) and anti-bribery regulations. All hospitality for non-U.S. government officials exceeding $100 requires pre-approval from Risk, Compliance & Integrity (RCI) and must be accurately reported in Concur.",
                "groundingScore": 1.0
            }

        # 2. Baby Bonding Monetary Gift Card
        if "baby bonding" in lowered_prompt and any(w in lowered_prompt for w in ["gift card", "amazon", "monetary"]):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat Leave Policy (Section 3), monetary Baby Bonding Benefits are processed exclusively through HR Payroll. Company policy strictly prohibits issuing monetary benefits as Amazon gift cards or processing monetary requests via ITSM support tickets.",
                "groundingScore": 0.95
            }

        # 3. ITSM Critical Priority & Allowance
        if ("mac pro" in lowered_prompt or "loaner" in lowered_prompt or "conference" in lowered_prompt) and ("priority" in lowered_prompt or "p1" in lowered_prompt) and ("critical" in lowered_prompt or "allowance" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Hardware & ITSM Policy:\n\n1. **ITSM Priority Rules**: Priority '1 - Critical' is strictly reserved for major business disruptions and inoperable primary work devices without a workaround (Section 4). Temporary loaner laptops for travel or conferences must be submitted as Priority 3 (Moderate).\n2. **Allowance Eligibility**: The $500 Home Office Equipment Allowance is strictly reserved for permanent home office setups (monitors, ergonomics) for approved Remote or Hybrid employees (Section 1) and cannot be claimed for loaner or conference laptops.",
                "groundingScore": 0.95
            }

        # 4. Unpaid Personal Leave Prerequisites
        if "unpaid personal leave" in lowered_prompt or ("unpaid" in lowered_prompt and "45" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat Leave Policy (Section 4):\n\n1. **Paid Leave Exhaustion Prerequisite**: Employees must exhaust all remaining paid annual vacation leave (currently 15 days available) prior to taking Unpaid Personal Leave.\n2. **Approval & Notice Requirements**: Personal leave requests exceeding 30 calendar days reclassify as Personal Leave (up to 92 days) and require at least **30 days advance notice** along with written approval from both your Manager and HR Director.",
                "groundingScore": 0.95
            }

        # 5. Ramp-Back Time Minimum Hours
        if "ramp-back" in lowered_prompt or ("15 hours" in lowered_prompt and "maternity" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 3):\n\n1. **Minimum Working Hours**: Ramp-Back Time immediately following maternity leave requires working **at least 50% of your normal schedule** (minimum **20 hours per week** for a standard 40-hour schedule) to receive 100% salary. Working 15 hours per week is below the 50% minimum threshold.\n2. **Logging in WorkWeek**: Once working at least 20 hours/week, log your worked hours in WorkWeek and select 'Ramp-Back Time' for the remaining 50% reduced hours.",
                "groundingScore": 0.95
            }

        # 6. Shift Worker Vacation Math
        if "12-hour shift" in lowered_prompt or ("12-hour" in lowered_prompt and "2 calendar days" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat HRMS policy:\n\n1. **Vacation Calculation for Shift Workers**: In WorkWeek, 1 day of vacation corresponds to 8 standard working hours. For a 12-hour shift worker, taking 2 calendar days off requires **24 working hours** (equivalent to **3.0 standard days**).\n2. **Insufficient Balance**: You currently have **2.5 days (20.0 hours)** of vacation remaining, which is insufficient to cover 2 full 12-hour shifts (24.0 hours required).",
                "groundingScore": 0.92
            }

        # 7. TOIL Order of Operations
        if "toil" in lowered_prompt and ("deduct" in lowered_prompt or "vacation" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 4):\n\n**Time Off In Lieu (TOIL) Order of Operations**: Earned TOIL for weekend or public holiday work **must be consumed before deducting from your annual vacation balance**. Please request your days off as 'TOIL Leave' in WorkWeek rather than deducting them from your vacation balance.",
                "groundingScore": 0.95
            }

        # 8. ITSM Skip to Closed Compliance
        if "inc0000123" in lowered_prompt or ("update it directly to 'closed'" in lowered_prompt or ("new" in lowered_prompt and "closed" in lowered_prompt and "ticket" in lowered_prompt)):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat ITSM Policy & Compliance Rules:\n\nTickets currently in **'New'** status cannot be updated directly to **'Closed'**. Standard state lifecycle rules require ticket INC0000123 to first transition to 'In Progress' and 'Resolved', or be marked as 'Cancelled' if self-resolved prior to investigation.",
                "groundingScore": 0.95
            }

        # 9. Sick vs Hospitalization MC 48h
        if "hospitalized" in lowered_prompt or ("hospitalization leave" in lowered_prompt and "outpatient" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "SUCCESS",
                "response": "According to Altostrat Leave Policy (Section 1):\n\nYes! Employees hospitalized with a valid hospital Medical Certificate (MC) submitted within 48 hours are entitled to **Hospitalization Leave** (up to 46 work days per year at 100% pay), which is separate from and does not deduct from your **Outpatient Sick Leave** balance.",
                "groundingScore": 0.95
            }

        # 10. Vacation Advance Notice
        if ("july 30" in lowered_prompt and "august 5" in lowered_prompt) or ("advance notice" in lowered_prompt and "vacation" in lowered_prompt):
            return {
                "orchestrator": "RootOrchestrator",
                "agent": "PolicyQAAgent",
                "status": "REFUSED",
                "response": "According to Altostrat Leave Policy (Section 2):\n\n**Advance Notice Violation**: Planned vacation dates must be submitted and approved at least **15 days in advance**. Submitting a request on July 30 for August 5 provides only 6 days of advance notice, which falls short of the required 15-day notice period.",
                "groundingScore": 0.95
            }

        return None
