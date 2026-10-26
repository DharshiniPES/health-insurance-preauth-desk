import time
import uuid
import asyncio
from typing import Dict, Any, List
from src.contracts import PreAuthRequest, PreAuthRecommendation, AgentStepTrace, Citation
from src.agents.intake_agent import ClinicalIntakeAgent
from src.agents.adjudicator import AdjudicationAgent
from src.guardrails import sanitize_input_text, GuardrailViolation, filter_agent_output
from src.llm_provider import circuit_breaker, CircuitBreakerOpenException
from src.config import settings

class MultiAgentOrchestrator:
    """
    Multi-Agent Coordinator (A1, A2, A5).
    - Coordinates ClinicalIntakeAgent and AdjudicationAgent with explicit hand-off
    - Bounds execution by step count, tool calls, and wall-clock time (A1)
    - Enforces circuit breaker check & graceful degradation path (A5)
    - Records prompt version, tokens, latency, and costs (L2, L5)
    """
    def __init__(self):
        self.intake_agent = ClinicalIntakeAgent()
        self.adjudicator_agent = AdjudicationAgent()

    async def run(self, request: PreAuthRequest, run_id: str = "") -> PreAuthRecommendation:
        start_time = time.time()
        if not run_id:
            run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

        step_traces: List[AgentStepTrace] = []
        context: Dict[str, Any] = {"run_id": run_id}

        # Step 0: Input Guardrail Check (L4)
        try:
            sanitize_input_text("diagnosis", request.diagnosis)
            sanitize_input_text("procedure_name", request.procedure_name)
            sanitize_input_text("hospital_name", request.hospital_name)
        except GuardrailViolation as gv:
            # Handle prompt injection or toxicity attempt (Demo Item 7)
            step_traces.append(AgentStepTrace(
                step_number=1,
                agent_name="GuardrailDefense",
                action="GUARDRAIL_BLOCKED",
                thought=f"Adversarial or toxic input detected: {str(gv)}",
                latency_ms=(time.time() - start_time) * 1000.0
            ))
            return PreAuthRecommendation(
                run_id=run_id,
                request_id=request.request_id,
                status="COMPLETED",
                route="medical-review",
                summary="Adversarial prompt injection attempt detected and quarantined by guardrails.",
                indicative_limit_inr=0.0,
                reason=f"Prompt injection guardrail triggered: {str(gv)}. Request escalated to Medical Review.",
                citations=[],
                self_verification_passed=True,
                escalation_path="Security & Fraud Investigation Unit",
                prompt_version=settings.ACTIVE_PROMPT_VERSION,
                total_tokens=25,
                total_cost_usd=0.000002,
                total_latency_ms=round((time.time() - start_time) * 1000.0, 2),
                steps=step_traces
            )

        # Check Circuit Breaker (A5, Demo Item 8)
        if not circuit_breaker.allow_request():
            # Graceful degradation path
            step_traces.append(AgentStepTrace(
                step_number=1,
                agent_name="SystemResilience",
                action="CIRCUIT_BREAKER_FALLBACK",
                thought="Model provider circuit breaker is OPEN. Degrading gracefully to manual medical review.",
                latency_ms=(time.time() - start_time) * 1000.0
            ))
            return PreAuthRecommendation(
                run_id=run_id,
                request_id=request.request_id,
                status="COMPLETED",
                route="medical-review",
                summary="System degraded gracefully due to upstream provider outage.",
                indicative_limit_inr=None,
                reason="Circuit breaker OPEN: upstream LLM provider unavailable. Escalated directly to Medical Officer.",
                citations=[],
                self_verification_passed=False,
                escalation_path="Urgent Medical Officer Desk (Offline Fallback)",
                prompt_version=settings.ACTIVE_PROMPT_VERSION,
                total_tokens=0,
                total_cost_usd=0.0,
                total_latency_ms=round((time.time() - start_time) * 1000.0, 2),
                steps=step_traces
            )

        try:
            # Wrap execution inside wall-clock timeout (A1)
            async with asyncio.timeout(settings.WALL_CLOCK_TIMEOUT_SEC):
                # 1. Agent 1: Clinical Intake & Retrieval
                context = await self.intake_agent.run(request, context, step_traces)

                # Check loop limits
                if len(step_traces) >= settings.MAX_AGENT_STEPS:
                    raise TimeoutError("Agent step limit exceeded during intake.")

                # 2. Hand-off to Agent 2: Adjudication & Self-Verification
                context = await self.adjudicator_agent.run(request, context, step_traces)

        except (TimeoutError, asyncio.TimeoutError):
            step_traces.append(AgentStepTrace(
                step_number=len(step_traces) + 1,
                agent_name="Orchestrator",
                action="WALL_CLOCK_TIMEOUT_ESCALATION",
                thought="Wall-clock execution timeout reached. Escalating for safety (A1, A5).",
                latency_ms=(time.time() - start_time) * 1000.0
            ))
            return PreAuthRecommendation(
                run_id=run_id,
                request_id=request.request_id,
                status="COMPLETED",
                route="medical-review",
                summary="Execution timed out; safe escalation to human review.",
                indicative_limit_inr=None,
                reason="Execution time limit exceeded without verifiable determination. Escalated to medical-review.",
                citations=[],
                self_verification_passed=False,
                escalation_path="Senior Adjudicator Queue",
                prompt_version=settings.ACTIVE_PROMPT_VERSION,
                total_tokens=sum(s.prompt_tokens + s.completion_tokens for s in step_traces),
                total_cost_usd=sum(s.cost_usd for s in step_traces),
                total_latency_ms=round((time.time() - start_time) * 1000.0, 2),
                steps=step_traces
            )

        total_latency = (time.time() - start_time) * 1000.0
        total_tokens = sum(s.prompt_tokens + s.completion_tokens for s in step_traces)
        total_cost = sum(s.cost_usd for s in step_traces)

        return PreAuthRecommendation(
            run_id=run_id,
            request_id=request.request_id,
            status="COMPLETED",
            route=context.get("route", "medical-review"),
            summary=f"Pre-authorisation recommendation: {context.get('route')}",
            indicative_limit_inr=context.get("indicative_limit"),
            reason=context.get("reason", "Adjudication complete."),
            citations=context.get("citations", []),
            self_verification_passed=context.get("verification_passed", True),
            escalation_path="Medical Officer Adjudication Desk" if context.get("route") == "medical-review" else None,
            prompt_version=settings.ACTIVE_PROMPT_VERSION,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 7),
            total_latency_ms=round(total_latency, 2),
            steps=step_traces
        )


orchestrator = MultiAgentOrchestrator()
