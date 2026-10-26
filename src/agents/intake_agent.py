import time
from datetime import date
from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.contracts import PreAuthRequest, AgentStepTrace, Citation
from src.tools import tools
from src.llm_provider import llm_client, PROMPTS
from src.config import settings

def calculate_policy_age_months(issue_date: date, admission_date: date) -> int:
    return (admission_date.year - issue_date.year) * 12 + (admission_date.month - issue_date.month)


SPECIFIC_WAITING_KEYWORDS = [
    "cataract", "hernia", "hydrocele", "hysterectomy", "cholelithiasis",
    "gall bladder stone", "calculus", "kidney stone", "joint replacement",
    "knee replacement", "hip replacement", "piles", "fistula", "sinusitis",
    "tonsillitis", "tympanoplasty", "osteoarthritis"
]

PERMANENT_EXCLUSION_KEYWORDS = [
    "cosmetic", "rhinoplasty", "aesthetic", "stem cell", "experimental",
    "unproven", "infertility", "ivf", "suicide", "hazardous"
]


class ClinicalIntakeAgent(BaseAgent):
    """
    Agent 1: Clinical Intake & Multi-Stage Dynamic Retrieval (F3, F4, A2).
    Implements Steps 1, 2, and 3 of Section 5 Design Approach:
    - Retrieves the primary provision that appears to apply
    - Determines if modifying provisions (waiting periods, exclusions) exist
    - Issues dynamic secondary searches derived from findings
    """
    def __init__(self):
        super().__init__(name="ClinicalIntakeAgent", role="Clinical & Retrieval Specialist")

    async def run(
        self,
        request: PreAuthRequest,
        context: Dict[str, Any],
        step_accumulator: List[AgentStepTrace]
    ) -> Dict[str, Any]:
        prompt_config = PROMPTS.get(settings.ACTIVE_PROMPT_VERSION, PROMPTS["v2"])
        sys_prompt = prompt_config["intake_prompt"]

        policy_age_months = calculate_policy_age_months(request.policy_issue_date, request.admission_date)
        context["policy_age_months"] = policy_age_months

        # Step 1: Admission Classification & Clinical Extraction
        step1_start = time.time()
        user_content = (
            f"Classify admission and clinical profile:\n"
            f"Procedure: {request.procedure_name}\n"
            f"Diagnosis: {request.diagnosis} (ICD-10: {request.icd10_code})\n"
            f"Type: {request.admission_type}\n"
            f"Policy Age: {policy_age_months} months (Issued: {request.policy_issue_date})"
        )
        llm_res1 = await llm_client.generate_response(sys_prompt, user_content)
        
        step_accumulator.append(AgentStepTrace(
            step_number=len(step_accumulator) + 1,
            agent_name=self.name,
            action="CLASSIFY_AND_EXTRACT",
            tool_name=None,
            thought=(
                f"Classified admission as '{request.admission_type}'. Extracted procedure '{request.procedure_name}'. "
                f"Calculated policy vintage: {policy_age_months} months."
            ),
            latency_ms=llm_res1["latency_ms"],
            cost_usd=llm_res1["cost_usd"],
            prompt_tokens=llm_res1["prompt_tokens"],
            completion_tokens=llm_res1["completion_tokens"]
        ))

        # Step 2: Primary Coverage Retrieval (Design Approach Step 1)
        step2_start = time.time()
        retrieved_clauses: Dict[str, Dict[str, Any]] = {}

        if request.admission_type == "day_care":
            dc_results = tools.search_daycare_schedule(request.procedure_name)
            tool_used = "search_daycare_schedule"
            tool_out = dc_results
            for item in dc_results:
                retrieved_clauses[item["clause_id"]] = item
            # Also fetch base day care cover clause
            base_cov = tools.lookup_clause("SEC-COV-DAYCARE")
            if base_cov:
                retrieved_clauses[base_cov["clause_id"]] = base_cov
        elif request.admission_type == "emergency":
            em_cov = tools.lookup_clause("SEC-COV-EMERGENCY")
            tool_used = "lookup_clause"
            tool_out = em_cov
            if em_cov:
                retrieved_clauses[em_cov["clause_id"]] = em_cov
            # Base inpatient
            inp_cov = tools.lookup_clause("SEC-COV-INP")
            if inp_cov:
                retrieved_clauses[inp_cov["clause_id"]] = inp_cov
        elif request.admission_type == "maternity":
            mat_cov = tools.lookup_clause("SEC-COV-MAT")
            tool_used = "lookup_clause"
            tool_out = mat_cov
            if mat_cov:
                retrieved_clauses[mat_cov["clause_id"]] = mat_cov
        else:
            search_res = tools.corpus_search(request.procedure_name, top_k=2)
            tool_used = "corpus_search"
            tool_out = search_res
            for item in search_res:
                retrieved_clauses[item["clause_id"]] = item
            inp_cov = tools.lookup_clause("SEC-COV-INP")
            if inp_cov:
                retrieved_clauses[inp_cov["clause_id"]] = inp_cov

        step_accumulator.append(AgentStepTrace(
            step_number=len(step_accumulator) + 1,
            agent_name=self.name,
            action="PRIMARY_COVER_RETRIEVAL",
            tool_name=tool_used,
            tool_input={"query": request.procedure_name, "admission_type": request.admission_type},
            tool_output=[c.get("clause_id") for c in retrieved_clauses.values()],
            thought="Step 1: Retrieved primary coverage clause(s) for the procedure.",
            latency_ms=(time.time() - step2_start) * 1000.0,
            cost_usd=0.0
        ))

        # Step 3: Dynamic Secondary Modifying Clause Search (Design Approach Steps 2 & 3)
        # Note: Prompt v1 (baseline) skips secondary modifying search (single-pass pipeline).
        # Prompt v2 executes full 2-stage dynamic search.
        step3_start = time.time()
        secondary_tools_called = []

        if settings.ACTIVE_PROMPT_VERSION != "v1":
            full_text = f"{request.procedure_name} {request.diagnosis}".lower()
            needs_specific_waiting_search = any(kw in full_text for kw in SPECIFIC_WAITING_KEYWORDS)
            needs_exclusion_search = any(kw in full_text for kw in PERMANENT_EXCLUSION_KEYWORDS)

            if needs_specific_waiting_search:
                modifying_clause = tools.lookup_clause("SEC-WAIT-24M-SPECIFIC")
                if modifying_clause:
                    retrieved_clauses[modifying_clause["clause_id"]] = modifying_clause
                    secondary_tools_called.append("lookup_clause: SEC-WAIT-24M-SPECIFIC")

            if needs_exclusion_search:
                excl_clause = tools.lookup_clause("SEC-EXCL-PERM")
                if excl_clause:
                    retrieved_clauses[excl_clause["clause_id"]] = excl_clause
                    secondary_tools_called.append("lookup_clause: SEC-EXCL-PERM")

            if request.admission_type == "maternity":
                mat_wait = tools.lookup_clause("SEC-WAIT-24M-MAT")
                if mat_wait:
                    retrieved_clauses[mat_wait["clause_id"]] = mat_wait
                    secondary_tools_called.append("lookup_clause: SEC-WAIT-24M-MAT")

            if request.ped_declared or "pre-existing" in full_text or "history" in full_text:
                ped_wait = tools.lookup_clause("SEC-WAIT-36M-PED")
                if ped_wait:
                    retrieved_clauses[ped_wait["clause_id"]] = ped_wait
                    secondary_tools_called.append("lookup_clause: SEC-WAIT-36M-PED")

            if policy_age_months < 1:
                wait_30d = tools.lookup_clause("SEC-WAIT-30D")
                if wait_30d:
                    retrieved_clauses[wait_30d["clause_id"]] = wait_30d
                    secondary_tools_called.append("lookup_clause: SEC-WAIT-30D")
        else:
            needs_specific_waiting_search = False
            needs_exclusion_search = False

        step_accumulator.append(AgentStepTrace(
            step_number=len(step_accumulator) + 1,
            agent_name=self.name,
            action="SECONDARY_MODIFYING_SEARCH",
            tool_name="dynamic_secondary_search",
            tool_input={"trigger_keywords_found": needs_specific_waiting_search or needs_exclusion_search},
            tool_output=secondary_tools_called,
            thought=(
                f"Step 2 & 3: Analyzed primary cover and identified modifying provisions. "
                f"Retrieved {len(secondary_tools_called)} secondary binding clauses: {secondary_tools_called}."
            ),
            latency_ms=(time.time() - step3_start) * 1000.0,
            cost_usd=0.0
        ))

        # Hand-off package to Agent 2
        context["retrieved_clauses"] = list(retrieved_clauses.values())
        context["needs_specific_waiting_search"] = needs_specific_waiting_search
        context["needs_exclusion_search"] = needs_exclusion_search

        return context
