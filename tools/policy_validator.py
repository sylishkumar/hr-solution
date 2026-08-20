"""
Policy Compliance Validator Engine
Enforces strict policy rules from the Altostrat Employee Policy Handbook BEFORE
any Human-in-the-Loop (HITL) action card or state mutation is generated.
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional
from tools.workweek_tools import get_employee_balances
from tools.policy_search_tool import search_hr_policies

class PolicyComplianceValidator:
    """
    Central validator enforcing policy bounds from Altostrat Employee Policy Handbook.
    """

    @staticmethod
    def validate_leave_request(
        employee_id: str,
        start_date_str: str,
        end_date_str: str,
        leave_type: str,
        days: float
    ) -> Tuple[bool, str]:
        """
        Validates a leave request against Handbook Section 1 (Sick), Section 2 (Vacation), Section 18 (Unpaid).
        Returns (is_allowed, policy_explanation).
        """
        today = datetime.now().date()
        leave_type_clean = leave_type.lower().strip()

        # Parse dates
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except Exception:
            # Default to tomorrow if unparseable
            start_dt = today
            end_dt = today

        # Rule 1: Chronological Validity
        if start_dt > end_dt:
            return False, "❌ **Chronological Error**: Start date cannot be after end date."

        notice_days = (start_dt - today).days

        # Rule 2: Vacation Leave Policy (Section 2 & Section 20)
        if "vacation" in leave_type_clean:
            # Notice Period: At least 15 days in advance
            if notice_days < 15:
                return False, (
                    f"❌ **Policy Restriction (Section 2.4 - Paid Vacation Leave)**:\n"
                    f"Planned vacation dates must be submitted and approved at least **15 days in advance**.\n"
                    f"Your requested start date (**{start_date_str}**) provides only **{max(0, notice_days)} day(s)** advance notice.\n"
                    f"Action cannot be initiated without prior manager policy exception."
                )

            # Balance Verification
            bal = get_employee_balances(employee_id)
            if "error" not in bal:
                vac_hours = bal.get("vacation_hours_remaining", 0.0)
                req_hours = days * 8.0
                if vac_hours < req_hours:
                    return False, (
                        f"❌ **Policy Restriction (Section 2.2 - System Constraints)**:\n"
                        f"Leave requests exceeding current accrued balance are automatically rejected.\n"
                        f"Requested: {req_hours} hours ({days} days). Available: {vac_hours} hours ({vac_hours/8.0:.1f} days)."
                    )

        # Rule 3: Sick Leave Policy (Section 1 & Section 19)
        elif "sick" in leave_type_clean:
            # MC Requirement Notice
            if days > 2.0:
                # Still allowed to request, but must attach policy MC warning
                pass

            bal = get_employee_balances(employee_id)
            if "error" not in bal:
                sick_hours = bal.get("sick_hours_remaining", 0.0)
                req_hours = days * 8.0
                if sick_hours < req_hours:
                    return False, (
                        f"❌ **Policy Restriction (Section 1.1 - Outpatient Sick Leave)**:\n"
                        f"Requested sick leave exceeds your annual remaining allowance.\n"
                        f"Requested: {req_hours} hours ({days} days). Available: {sick_hours} hours ({sick_hours/8.0:.1f} days)."
                    )

        # Rule 4: Personal / Unpaid Leave (Section 18)
        elif "unpaid" in leave_type_clean or "personal" in leave_type_clean:
            if days > 30 and notice_days < 30:
                return False, (
                    f"❌ **Policy Restriction (Section 18.3 - Personal Leave)**:\n"
                    f"Personal leaves exceeding 30 days require at least **30 days advance notice** and manager/director approval."
                )

        return True, "✅ Policy Validation Passed: Request complies with all Handbook terms."

    @staticmethod
    def validate_travel_request(departure_date_str: str, daily_amount_usd: float) -> Tuple[bool, str]:
        """
        Validates travel bookings against Section 4 (Travel & Expense Guidelines).
        """
        today = datetime.now().date()
        try:
            dep_dt = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
            notice_days = (dep_dt - today).days
        except Exception:
            notice_days = 1

        if notice_days < 21:
            return False, (
                f"❌ **Policy Restriction (Section 4.1 - Travel Guidelines)**:\n"
                f"All airfare and hotel bookings must be completed at least **3 weeks (21 days) in advance** to secure reasonable rates.\n"
                f"Your requested departure ({departure_date_str}) is only **{max(0, notice_days)} day(s)** away."
            )

        if daily_amount_usd > 120.0:
            return False, (
                f"❌ **Policy Restriction (Section 4.4 - Meal Allowances)**:\n"
                f"Reimbursement for individual business meals is capped at **US $120 per day**."
            )

        return True, "✅ Policy Validation Passed: Travel request complies with T&E Guidelines."
