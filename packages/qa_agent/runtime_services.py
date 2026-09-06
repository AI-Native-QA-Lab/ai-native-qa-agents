"""Deterministic v0.1 runtime service boundaries."""
from .runtime import AgentState, Observation

class ReviewPlanner:
    def plan(self) -> tuple[str, ...]: return ("detect", "inspect-diff", "discover-tests", "run-rules", "verify-and-gate")
class ActionExecutor:
    def execute(self, iteration: int, action: str) -> Observation: return Observation(f"OBS-{iteration:03d}", action, action)
class Observer:
    def record(self, state: AgentState, observation: Observation) -> None: state.observations.append(observation)
class Evaluator:
    def sufficient(self, evidence_count: int, finding_count: int) -> bool: return finding_count == 0 or evidence_count >= finding_count
class EvidenceVerifier:
    def verify(self, finding_evidence_ids: list[str], evidence_ids: set[str]) -> str: return "verified" if finding_evidence_ids and set(finding_evidence_ids) <= evidence_ids else "unverified"
