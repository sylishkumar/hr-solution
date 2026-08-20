"""
WorkWeek HCM Mock MCP Service
Provides in-memory mock endpoints and API methods matching the OpenAPI schema in section 5.4.1 of SDD.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

# In-memory database
EMPLOYEE_PROFILES: Dict[str, Dict[str, Any]] = {
    "EMP1024": {
        "employee_id": "EMP1024",
        "name": "Aish Prabhat",
        "email": "aishprabhat@google.com",
        "role": "Staff Software Engineer",
        "home_address": "123 Tech Blvd, Austin, TX 78701",
        "phone_number": "+1-512-555-0199",
        "manager_id": "EMP0012",
        "status": "ACTIVE"
    },
    "EMP2048": {
        "employee_id": "EMP2048",
        "name": "Jane Doe",
        "email": "janedoe@google.com",
        "role": "Product Manager",
        "home_address": "456 Innovation Way, San Jose, CA 95110",
        "phone_number": "+1-408-555-0122",
        "manager_id": "EMP0012",
        "status": "ACTIVE"
    }
}

LEAVE_BALANCES: Dict[str, Dict[str, float]] = {
    "EMP1024": {
        "vacation_hours_remaining": 120.0,
        "sick_hours_remaining": 48.0,
        "vacation_hours_used": 40.0,
        "sick_hours_used": 8.0
    },
    "EMP2048": {
        "vacation_hours_remaining": 16.0,  # Low balance for testing insufficient balance
        "sick_hours_remaining": 24.0,
        "vacation_hours_used": 104.0,
        "sick_hours_used": 24.0
    }
}

TIME_OFF_REQUESTS: List[Dict[str, Any]] = [
    {
        "request_id": "REQ-1001",
        "employee_id": "EMP1024",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05",
        "leave_type": "Vacation",
        "days": 5.0,
        "status": "CONFIRMED"
    }
]

class WorkWeekService:
    @staticmethod
    def get_current_employee_id(email: str = "aishprabhat@google.com") -> Dict[str, Any]:
        for emp_id, profile in EMPLOYEE_PROFILES.items():
            if profile["email"] == email:
                return {"employee_id": emp_id, "email": email, "status": profile["status"]}
        return {"employee_id": "EMP1024", "email": email, "status": "ACTIVE"}

    @staticmethod
    def get_employee_balances(employee_id: str) -> Dict[str, Any]:
        if employee_id not in LEAVE_BALANCES:
            return {"error": f"Employee {employee_id} not found", "code": 404}
        bal = LEAVE_BALANCES[employee_id]
        return {
            "employee_id": employee_id,
            "vacation_hours_remaining": bal["vacation_hours_remaining"],
            "sick_hours_remaining": bal["sick_hours_remaining"]
        }

    @staticmethod
    def request_time_off(employee_id: str, start_date: str, end_date: str, leave_type: str, days: float) -> Dict[str, Any]:
        if employee_id not in LEAVE_BALANCES:
            return {"error": f"Employee {employee_id} not found", "code": 404}
        
        bal = LEAVE_BALANCES[employee_id]
        requested_hours = days * 8.0
        
        if leave_type.lower() == "vacation" and bal["vacation_hours_remaining"] < requested_hours:
            return {
                "error": "INSUFFICIENT_BALANCE",
                "message": f"Requested {requested_hours} hours, but only {bal['vacation_hours_remaining']} hours available.",
                "code": 422
            }
        
        if leave_type.lower() == "vacation":
            bal["vacation_hours_remaining"] -= requested_hours
            bal["vacation_hours_used"] += requested_hours
        
        req_id = f"REQ-{len(TIME_OFF_REQUESTS) + 9900}"
        record = {
            "request_id": req_id,
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days": days,
            "status": "CONFIRMED",
            "created_at": datetime.now().isoformat()
        }
        TIME_OFF_REQUESTS.append(record)
        return {
            "status": "CONFIRMED",
            "request_id": req_id,
            "employee_id": employee_id,
            "days_deducted": days,
            "remaining_vacation_hours": bal["vacation_hours_remaining"]
        }

    @staticmethod
    def get_personal_info(employee_id: str) -> Dict[str, Any]:
        if employee_id not in EMPLOYEE_PROFILES:
            return {"error": f"Employee {employee_id} not found", "code": 404}
        p = EMPLOYEE_PROFILES[employee_id]
        return {
            "employee_id": employee_id,
            "name": p["name"],
            "email": p["email"],
            "home_address": p["home_address"],
            "phone_number": p["phone_number"]
        }

    @staticmethod
    def update_personal_info(employee_id: str, address: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
        if employee_id not in EMPLOYEE_PROFILES:
            return {"error": f"Employee {employee_id} not found", "code": 404}
        p = EMPLOYEE_PROFILES[employee_id]
        if address:
            p["home_address"] = address
        if phone:
            p["phone_number"] = phone
        return {
            "status": "UPDATED",
            "employee_id": employee_id,
            "address": p["home_address"],
            "phone": p["phone_number"],
            "updated_at": datetime.now().isoformat()
        }

    @staticmethod
    def get_leave_requests(employee_id: str) -> Dict[str, Any]:
        reqs = [r for r in TIME_OFF_REQUESTS if r["employee_id"] == employee_id]
        return {"employee_id": employee_id, "requests": reqs}

    @staticmethod
    def cancel_leave_request(employee_id: str, request_id: str) -> Dict[str, Any]:
        for r in TIME_OFF_REQUESTS:
            if r["request_id"] == request_id and r["employee_id"] == employee_id:
                if r["status"] == "CANCELLED":
                    return {"message": "Request already cancelled", "status": "CANCELLED"}
                r["status"] = "CANCELLED"
                # refund hours
                refund_hours = r["days"] * 8.0
                if r["leave_type"].lower() == "vacation" and employee_id in LEAVE_BALANCES:
                    LEAVE_BALANCES[employee_id]["vacation_hours_remaining"] += refund_hours
                    LEAVE_BALANCES[employee_id]["vacation_hours_used"] -= refund_hours
                return {
                    "status": "CANCELLED",
                    "request_id": request_id,
                    "days_refunded": r["days"]
                }
        return {"error": f"Request {request_id} not found for employee {employee_id}", "code": 404}
