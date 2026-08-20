"""
ServiceImmediately ITSM Mock MCP Service
Provides in-memory mock endpoints and API methods matching OpenAPI schema in section 5.4.2 of SDD.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

# In-memory ticket store
INCIDENT_TICKETS: List[Dict[str, Any]] = [
    {
        "ticket_id": "INC908100",
        "requested_by": "EMP1024",
        "category": "Hardware",
        "short_description": "Laptop battery replacement",
        "priority": "3 - Moderate",
        "status": "In Progress",
        "assignment_group": "Hardware Support",
        "comments": [
            {"author": "System", "comment_text": "Ticket opened.", "timestamp": "2026-08-10T10:00:00Z"}
        ],
        "created_at": "2026-08-10T10:00:00Z"
    }
]

class ServiceImmediatelyService:
    @staticmethod
    def list_tickets(employee_id: str) -> Dict[str, Any]:
        user_tickets = [t for t in INCIDENT_TICKETS if t["requested_by"] == employee_id]
        return {"tickets": user_tickets}

    @staticmethod
    def create_ticket(
        requested_by: str,
        category: str,
        short_description: str,
        priority: str = "3 - Moderate",
        assignment_group: str = "Service Desk"
    ) -> Dict[str, Any]:
        # Check duplicate submission within 5 mins (mock check)
        for t in INCIDENT_TICKETS:
            if (t["requested_by"] == requested_by and
                t["short_description"].lower() == short_description.lower() and
                t["status"] not in ["Resolved", "Closed"]):
                return {
                    "error": "DUPLICATE_TICKET",
                    "message": f"A similar ticket {t['ticket_id']} is already open.",
                    "code": 409
                }

        ticket_id = f"INC{908124 + len(INCIDENT_TICKETS)}"
        ticket = {
            "ticket_id": ticket_id,
            "requested_by": requested_by,
            "category": category,
            "short_description": short_description,
            "priority": priority,
            "status": "New",
            "assignment_group": assignment_group,
            "comments": [
                {"author": "System", "comment_text": "Ticket created via HR Agentic Assistant.", "timestamp": datetime.now().isoformat()}
            ],
            "created_at": datetime.now().isoformat()
        }
        INCIDENT_TICKETS.append(ticket)
        return {
            "status": "CREATED",
            "ticket_id": ticket_id,
            "requested_by": requested_by,
            "priority": priority,
            "assignment_group": assignment_group,
            "created_at": ticket["created_at"]
        }

    @staticmethod
    def add_ticket_comment(ticket_id: str, author: str, comment: str) -> Dict[str, Any]:
        for t in INCIDENT_TICKETS:
            if t["ticket_id"] == ticket_id:
                comment_obj = {
                    "author": author,
                    "comment_text": comment,
                    "timestamp": datetime.now().isoformat()
                }
                t["comments"].append(comment_obj)
                return {
                    "status": "COMMENT_ADDED",
                    "ticket_id": ticket_id,
                    "author": author,
                    "timestamp": comment_obj["timestamp"]
                }
        return {"error": f"Ticket {ticket_id} not found", "code": 404}

    @staticmethod
    def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> Dict[str, Any]:
        valid_statuses = ["New", "In Progress", "Resolved", "Closed"]
        if status not in valid_statuses:
            return {"error": f"Invalid status {status}. Must be one of {valid_statuses}", "code": 400}
            
        for t in INCIDENT_TICKETS:
            if t["ticket_id"] == ticket_id:
                t["status"] = status
                if resolution_notes:
                    t["comments"].append({
                        "author": updated_by,
                        "comment_text": f"Status updated to {status}. Notes: {resolution_notes}",
                        "timestamp": datetime.now().isoformat()
                    })
                return {
                    "status": "UPDATED",
                    "ticket_id": ticket_id,
                    "current_status": status,
                    "updated_by": updated_by
                }
        return {"error": f"Ticket {ticket_id} not found", "code": 404}
