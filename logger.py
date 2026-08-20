"""
Central Structured Logger for Enterprise HR Agentic Solution
Logs turn execution, policy validation, HITL confirmations, and MCP client calls.
"""

import os
import sys
import logging

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "hr_agentic_system.log")

# Configure logger
logger = logging.getLogger("HRAgenticSolution")
logger.setLevel(logging.INFO)

# Console Handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)

# File Handler
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(ch)
    logger.addHandler(fh)

def log_event(event_type: str, details: dict):
    """Utility to emit structured log events."""
    logger.info(f"[{event_type.upper()}] {details}")
