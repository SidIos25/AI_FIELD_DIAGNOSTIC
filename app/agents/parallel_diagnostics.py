from google.adk.agents import ParallelAgent
from app.agents.diagnostic.pattern_agent import pattern_agent
from app.agents.diagnostic.knowledge_agent import knowledge_agent

parallel_diagnostics = ParallelAgent(
    name="ParallelDiagnostics",
    sub_agents=[pattern_agent, knowledge_agent]
)
