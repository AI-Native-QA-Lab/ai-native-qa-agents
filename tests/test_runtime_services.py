from qa_agent.runtime import AgentState
from qa_agent.runtime_services import ActionExecutor, EvidenceVerifier, Evaluator, Observer, ReviewPlanner

def test_runtime_services_define_v01_control_boundaries() -> None:
    state = AgentState("t", "review")
    observation = ActionExecutor().execute(1, "detect")
    Observer().record(state, observation)
    assert ReviewPlanner().plan()[0] == "detect"
    assert state.observations == [observation]
    assert Evaluator().sufficient(1, 1)
    assert EvidenceVerifier().verify(["EV-001"], {"EV-001"}) == "verified"
