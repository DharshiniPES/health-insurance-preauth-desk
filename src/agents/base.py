from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.contracts import PreAuthRequest, AgentStepTrace

class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    async def run(
        self,
        request: PreAuthRequest,
        context: Dict[str, Any],
        step_accumulator: List[AgentStepTrace]
    ) -> Dict[str, Any]:
        """Executes the agent's task, updating context and step accumulator."""
        pass
