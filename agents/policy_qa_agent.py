"""
PolicyQAAgent Sub-Agent
Specialized read-only sub-agent for querying corporate policy handbooks using Policy Search Grounding.
"""

from typing import Dict, Any
from tools.policy_search_tool import search_hr_policies

class PolicyQAAgent:
    """
    Sub-agent responsible for answering general HR, leave, hardware, and expense policy inquiries.
    Strictly read-only with zero mutating capabilities.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def process_turn(self, query: str, user_role: str = "roles/hr.employee") -> Dict[str, Any]:
        # Perform policy search grounding check
        grounding_result = search_hr_policies(query, user_role=user_role)
        
        if grounding_result.get("refusal"):
            return {
                "agent": "PolicyQAAgent",
                "groundingScore": grounding_result["groundingScore"],
                "status": "REFUSED",
                "response": grounding_result["message"],
                "citations": []
            }
        
        results = grounding_result.get("results", [])
        citations = grounding_result.get("groundingSupports", [])
        
        if not results:
            return {
                "agent": "PolicyQAAgent",
                "groundingScore": grounding_result["groundingScore"],
                "status": "REFUSED",
                "response": "I could not find an official corporate policy matching your request.",
                "citations": []
            }
            
        doc = results[0]
        answer_text = f"According to the {doc['document']} ({doc['section']}):\n\n{doc['text']}"
        
        return {
            "agent": "PolicyQAAgent",
            "groundingScore": grounding_result["groundingScore"],
            "status": "SUCCESS",
            "response": answer_text,
            "citations": citations
        }
