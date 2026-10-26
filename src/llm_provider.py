import os
import time
import math
import asyncio
from typing import Dict, Any, Optional, Tuple
from src.config import settings

COST_PER_1M_INPUT_TOKENS_USD = 0.075
COST_PER_1M_OUTPUT_TOKENS_USD = 0.30

# Prompt Templates (Versioned Artifacts - L2)
PROMPTS = {
    "v1": {
        "version": "v1.0-concise",
        "intake_prompt": (
            "You are a Clinical Intake Specialist. Given the pre-auth request, identify whether "
            "it is planned surgical, day care, emergency, or maternity. Extract procedure and vintage."
        ),
        "adjudication_prompt": (
            "You are an Insurance Coverage Adjudicator. Based on retrieved clauses and policy age, "
            "state if covered and give an indicative limit. Return route: approve-recommended, query-to-hospital, or medical-review."
        )
    },
    "v2": {
        "version": "v2.0-verified-cot",
        "intake_prompt": (
            "You are a Senior Medical Officer & Clinical Intake Agent. Classify the admission type, "
            "calculate exact policy vintage in months, determine if the diagnosis or procedure is subject to "
            "specific waiting periods (24m/36m) or exclusions, and retrieve BOTH the cover clause AND the modifying "
            "waiting-period/exclusion clauses before hand-off."
        ),
        "adjudication_prompt": (
            "You are an Adjudication & Self-Verification Agent. Adjudicate the coverage position by verifying "
            "that every claim is strictly grounded in retrieved passages. "
            "Crucial Rule: If a procedure has a specific waiting period (e.g. Cataract 24 months, Hernia 24 months), "
            "verify whether policy age >= waiting period. Cite BOTH the coverage clause and the waiting period clause. "
            "If policy age < waiting period or unverified, route to 'medical-review'."
        )
    }
}


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 3, reset_timeout: float = 30.0):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.force_open = False  # Allows manual demonstration of breaker opening (Demo Item 8)

    def record_success(self):
        self.consecutive_failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.fail_threshold:
            self.state = "OPEN"

    def allow_request(self) -> bool:
        if self.force_open:
            return False
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False


circuit_breaker = CircuitBreaker(
    fail_threshold=settings.CIRCUIT_BREAKER_FAIL_THRESHOLD,
    reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT_SEC
)


class CostTracker:
    @staticmethod
    def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
        cost = (prompt_tokens / 1_000_000.0) * COST_PER_1M_INPUT_TOKENS_USD + \
               (completion_tokens / 1_000_000.0) * COST_PER_1M_OUTPUT_TOKENS_USD
        return round(cost, 7)


class LLMClient:
    """Pluggable LLM Client with Circuit Breaker, Retries, and Fallback (A5, L5, D6)."""

    def __init__(self):
        self.prompt_version = settings.ACTIVE_PROMPT_VERSION

    async def generate_response(
        self,
        system_instruction: str,
        user_prompt: str,
        simulated_delay_sec: float = 0.03
    ) -> Dict[str, Any]:
        start_ts = time.time()

        # Check circuit breaker
        if not circuit_breaker.allow_request():
            raise CircuitBreakerOpenException(
                "Circuit breaker is OPEN. Upstream model provider temporarily unavailable."
            )

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                # Execute based on provider mode
                if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
                    # In real Gemini mode, calls Gemini API
                    result = await self._call_gemini(system_instruction, user_prompt)
                else:
                    # Deterministic Stub Provider (D6, A5)
                    result = await self._call_stub(system_instruction, user_prompt, simulated_delay_sec)

                circuit_breaker.record_success()
                latency_ms = (time.time() - start_ts) * 1000.0
                result["latency_ms"] = round(latency_ms, 2)
                return result

            except Exception as e:
                last_error = e
                circuit_breaker.record_failure()
                if attempt < settings.MAX_RETRIES:
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))

        raise last_error

    async def _call_stub(self, system_instruction: str, user_prompt: str, delay_sec: float) -> Dict[str, Any]:
        """High-performance realistic stub service (D6)."""
        await asyncio.sleep(delay_sec)
        # Approximate tokens
        prompt_tokens = len(system_instruction.split()) + len(user_prompt.split()) + 20
        completion_tokens = 45
        cost = CostTracker.calculate_cost(prompt_tokens, completion_tokens)

        return {
            "content": "Adjudication reasoning processed successfully.",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost,
            "provider": "stub-v1"
        }

    async def _call_gemini(self, system_instruction: str, user_prompt: str) -> Dict[str, Any]:
        # Simple HTTP REST call or SDK call
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.DEFAULT_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}]
        }
        async with httpx.AsyncClient(timeout=settings.CALL_TIMEOUT_SEC) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            cand = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            p_tok = usage.get("promptTokenCount", 100)
            c_tok = usage.get("candidatesTokenCount", 50)
            cost = CostTracker.calculate_cost(p_tok, c_tok)
            return {
                "content": cand,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "cost_usd": cost,
                "provider": "gemini"
            }


llm_client = LLMClient()
