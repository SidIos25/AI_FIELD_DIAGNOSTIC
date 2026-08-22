from google.adk.agents import SequentialAgent, ParallelAgent

from app.agents.parallel_diagnostics import parallel_diagnostics
from app.agents.synthesis.root_cause_synthesizer import synthesizer_agent
from app.agents.decision.repair_planner_agent import planner_agent
from app.agents.decision.escalation_agent import escalation_agent

decision_layer = ParallelAgent(
    name="DecisionLayer",
    sub_agents=[planner_agent, escalation_agent]
)

root_agent = SequentialAgent(
    name="FieldDiagnosticRootAgent",
    sub_agents=[
        parallel_diagnostics,
        synthesizer_agent,
        decision_layer
    ]
)
