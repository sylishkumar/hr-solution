import os

# Central Configuration
PROJECT_ID = os.getenv("GCP_PROJECT", "hr-agentic-solution")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Models
ORCHESTRATOR_MODEL = "gemini-2.5-pro"
SUBAGENT_MODEL = "gemini-2.5-flash"
EVAL_JUDGE_MODEL = "gemini-2.5-pro"

# Grounding & Security Thresholds
GROUNDING_SCORE_THRESHOLD = 0.85
PER_USER_RATE_LIMIT_PER_MIN = 50

# Live FastMCP SaaS Backend
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://mock-saas.aishprabhat.demo.altostrat.com")
WORKWEEK_MCP_URL = f"{MCP_BASE_URL}/work-week/mcp/"
SERVICE_IMMEDIATELY_MCP_URL = f"{MCP_BASE_URL}/service-immediately/mcp/"
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "mcp_Te-_-1ucfT9JanR2H9OAiTs2lA8pBLBXMgkq2l5wfOY")
