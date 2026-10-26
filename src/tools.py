import json
from typing import Dict, Any, List, Optional
from src.vector_store import policy_index
from src.contracts import PreAuthRequest

class ToolRegistry:
    """Registry of tools exposed to agents (A1)."""

    @staticmethod
    def corpus_search(query: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches the insurance policy corpus for matching clauses or terms."""
        return policy_index.search(query=query, top_k=top_k, category_filter=category_filter)

    @staticmethod
    def lookup_clause(clause_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific policy clause by its unique clause ID (e.g. SEC-COV-INP, SEC-WAIT-24M-SPECIFIC)."""
        return policy_index.lookup_clause(clause_id=clause_id)

    @staticmethod
    def get_request_field(req: PreAuthRequest, field_name: str) -> Any:
        """Looks up a specific field from the pre-authorisation request payload."""
        data = req.model_dump()
        return data.get(field_name, f"Field '{field_name}' not found")

    @staticmethod
    def search_daycare_schedule(procedure_name: str) -> List[Dict[str, Any]]:
        """Searches the official Day Care Procedure Schedule for coverage eligibility and linked clauses."""
        return policy_index.search(query=procedure_name, top_k=2, category_filter="daycare")

    @staticmethod
    def check_sublimit_and_room_rent(
        procedure_name: str,
        sum_insured: float,
        daily_room_rent: float,
        room_category: str,
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Calculates applicable room rent limits and procedure specific caps."""
        result = {
            "eligible_amount": estimated_cost,
            "deductions": 0.0,
            "applicable_clauses": [],
            "notes": []
        }

        # Check Room Rent Sub-Limit (Clause 4.1): 1% of Sum Insured per day
        if room_category not in ["day_care", "icu"]:
            eligible_daily_rent = 0.01 * sum_insured
            if daily_room_rent > eligible_daily_rent:
                result["applicable_clauses"].append("SEC-SUBLIM-ROOM")
                result["notes"].append(
                    f"Room rent capping triggered: requested Rs. {daily_room_rent}/day exceeds "
                    f"eligible 1% limit (Rs. {eligible_daily_rent}/day). Proportionate deduction applies."
                )

        # Check Cataract Specific Sub-Limit (Clause 4.2): min(Rs. 40,000, 10% of SI)
        if "cataract" in procedure_name.lower():
            cataract_cap = min(40000.0, 0.10 * sum_insured)
            result["applicable_clauses"].append("SEC-SUBLIM-CATARACT")
            if estimated_cost > cataract_cap:
                result["deductions"] += (estimated_cost - cataract_cap)
                result["eligible_amount"] = cataract_cap
                result["notes"].append(
                    f"Cataract sub-limit (SEC-SUBLIM-CATARACT) applied: capped at Rs. {cataract_cap:.0f}."
                )

        # Check Joint Replacement Sub-Limit (Clause 4.3): min(Rs. 2,50,000, 50% of SI)
        if any(w in procedure_name.lower() for w in ["knee replacement", "hip replacement", "joint replacement"]):
            joint_cap = min(250000.0, 0.50 * sum_insured)
            result["applicable_clauses"].append("SEC-SUBLIM-JOINT")
            if estimated_cost > joint_cap:
                result["deductions"] += (estimated_cost - joint_cap)
                result["eligible_amount"] = joint_cap
                result["notes"].append(
                    f"Joint replacement sub-limit (SEC-SUBLIM-JOINT) applied: capped at Rs. {joint_cap:.0f}."
                )

        return result


tools = ToolRegistry()
