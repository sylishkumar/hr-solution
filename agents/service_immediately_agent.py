"""
ServiceImmediatelyAgent Sub-Agent
Specialized sub-agent for IT Service Management (ITSM) operations.
"""

from typing import Dict, Any, Optional
from tools.service_immediately_tools import (
    list_tickets,
    create_ticket,
    add_ticket_comment,
    update_ticket_status
)

class ServiceImmediatelyAgent:
    """
    Sub-agent for IT Service Management (ITSM) tasks: ticket creation, status queries, comments.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def get_tickets(self, employee_id: str) -> Dict[str, Any]:
        res = list_tickets(employee_id)
        tickets = res.get("tickets", [])
        if not tickets:
            msg = "You currently have no open IT support tickets."
            return {"agent": "ServiceImmediatelyAgent", "status": "SUCCESS", "response": msg, "message": msg}
            
        summary_lines = [f"- Ticket {t['ticket_id']} ({t.get('category', 'IT')}): {t['short_description']} | Status: {t['status']} | Priority: {t['priority']}" for t in tickets]
        msg = "Here are your current IT support tickets:\n" + "\n".join(summary_lines)
        return {"agent": "ServiceImmediatelyAgent", "status": "SUCCESS", "response": msg, "message": msg, "data": res}

    def propose_ticket_creation(
        self,
        requested_by: str,
        category: str,
        short_description: str,
        priority: str = "3 - Moderate",
        assignment_group: str = "Service Desk"
    ) -> Dict[str, Any]:
        return {
            "agent": "ServiceImmediatelyAgent",
            "status": "HITL_REQUIRED",
            "action": "create_ticket",
            "parameters": {
                "requested_by": requested_by,
                "category": category,
                "short_description": short_description,
                "priority": priority,
                "assignment_group": assignment_group
            },
            "card_summary": f"Confirm creating IT support ticket for '{short_description}' (Category: {category}, Priority: {priority})."
        }

    def execute_ticket_creation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        requested_by = parameters.get("requested_by", "EMP1024")
        category = parameters.get("category", "Hardware")
        short_description = parameters.get("short_description", "IT Service Request")
        priority = parameters.get("priority", "3 - Moderate")
        assignment_group = parameters.get("assignment_group", "Service Desk")

        res = create_ticket(
            requested_by=requested_by,
            category=category,
            short_description=short_description,
            priority=priority,
            assignment_group=assignment_group
        )
        
        if "error" in res:
            err_msg = res.get("message", res["error"])
            return {
                "agent": "ServiceImmediatelyAgent",
                "status": "ERROR",
                "response": f"Failed to create ticket: {err_msg}",
                "message": f"Failed to create ticket: {err_msg}"
            }
            
        ticket_id = res.get("ticket_id", "INC908125")
        assign_grp = res.get("assignment_group", assignment_group)
        msg = f"Hardware/IT ticket {ticket_id} created successfully and assigned to {assign_grp}."
        
        return {
            "agent": "ServiceImmediatelyAgent",
            "status": "SUCCESS",
            "response": msg,
            "message": msg,
            "data": res
        }

    def add_comment(self, ticket_id: str, author: str, comment: str) -> Dict[str, Any]:
        res = add_ticket_comment(ticket_id, author, comment)
        if "error" in res:
            return {"agent": "ServiceImmediatelyAgent", "status": "ERROR", "response": res["error"], "message": res["error"]}
        msg = f"Comment added to ticket {ticket_id}."
        return {"agent": "ServiceImmediatelyAgent", "status": "SUCCESS", "response": msg, "message": msg, "data": res}

    def set_status(self, ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> Dict[str, Any]:
        res = update_ticket_status(ticket_id, status, resolution_notes, updated_by)
        if "error" in res:
            return {"agent": "ServiceImmediatelyAgent", "status": "ERROR", "response": res["error"], "message": res["error"]}
        msg = f"Ticket {ticket_id} status updated to {status}."
        return {"agent": "ServiceImmediatelyAgent", "status": "SUCCESS", "response": msg, "message": msg, "data": res}
