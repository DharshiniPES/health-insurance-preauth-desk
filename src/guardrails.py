import re
from typing import Tuple, List

# Adversarial prompt injection markers
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+)?unrestricted", re.IGNORECASE),
    re.compile(r"dan\s+mode", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(policy|rules|waiting\s+periods|exclusions)", re.IGNORECASE),
    re.compile(r"authorise\s+(full\s+)?claim\s+immediately", re.IGNORECASE),
    re.compile(r"approve\s+recommended\s+without\s+checks?", re.IGNORECASE),
    re.compile(r"bypass\s+(verification|guardrails?)", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"print\s+(secret|password|key|token)", re.IGNORECASE),
]

# Simple toxic/abusive markers
TOXICITY_PATTERNS = [
    re.compile(r"\b(threat|kill|harm|abuse|corrupt|fraud|bribe|illegal)\b", re.IGNORECASE),
]

DISALLOWED_OUTPUT_PHRASES = [
    re.compile(r"insurer\s+guarantees\s+payment", re.IGNORECASE),
    re.compile(r"legally\s+binding\s+commitment", re.IGNORECASE),
    re.compile(r"irrevocably\s+approved", re.IGNORECASE),
]

MANDATORY_DISCLAIMER = (
    "Pre-authorisation recommendation only based on preliminary clinical summary. "
    "Final coverage determination and admissible claim amount rests solely with the Medical Officer / TPA."
)

class GuardrailViolation(Exception):
    def __init__(self, message: str, violation_type: str):
        super().__init__(message)
        self.violation_type = violation_type


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """Scans free-text fields for adversarial prompt injection attempts."""
    if not text:
        return False, ""
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Prompt injection pattern detected: '{match.group(0)}'"
    return False, ""


def detect_toxicity(text: str) -> Tuple[bool, str]:
    """Scans text for toxic or abusive language."""
    if not text:
        return False, ""
    for pattern in TOXICITY_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Toxic or disallowed terminology flagged: '{match.group(0)}'"
    return False, ""


def sanitize_input_text(field_name: str, text: str) -> str:
    """Validates and sanitizes free-text fields before passing to LLM or tools."""
    is_inj, inj_msg = detect_prompt_injection(text)
    if is_inj:
        raise GuardrailViolation(f"Field '{field_name}' rejected: {inj_msg}", "PROMPT_INJECTION")
    
    is_tox, tox_msg = detect_toxicity(text)
    if is_tox:
        # Flag but strip or raise depending on policy
        raise GuardrailViolation(f"Field '{field_name}' flagged for content policy: {tox_msg}", "TOXICITY")
    
    return text.strip()


def filter_agent_output(output_text: str) -> str:
    """Ensures output does not exceed system authority and contains required disclaimer."""
    cleaned = output_text
    for pattern in DISALLOWED_OUTPUT_PHRASES:
        cleaned = pattern.sub("[AUTHORITY BOUNDARY ENFORCED: PRE-AUTH RECOMMENDATION ONLY]", cleaned)
    
    if MANDATORY_DISCLAIMER not in cleaned:
        cleaned = f"{cleaned}\n\n[DISCLAIMER]: {MANDATORY_DISCLAIMER}"
    
    return cleaned
