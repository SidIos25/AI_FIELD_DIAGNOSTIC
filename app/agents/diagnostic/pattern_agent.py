from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from app.models import get_provider_timeout_seconds
from app.tools.get_sensor_context import get_sensor_context

pattern_agent = LlmAgent(
    name="PatternDiagnosticAgent",
    model= LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=get_provider_timeout_seconds()),
    instruction="""
You are a failure pattern diagnostic agent.
Goal: identify the most likely failure type using sensor patterns for the given device and error_code.

Process:
1) Call get_sensor_context(device, error_code).
2) Use only the tool output as evidence.
3) If tool output is missing or low quality, return "insufficient_data".

Return JSON:
{
  "failure_type": "...",
  "evidence": ["..."],
  "confidence": 0.0,
  "assumptions": ["..."],
  "data_gaps": ["..."],
  "next_steps": ["..."]
}

Rules:
- confidence must be between 0 and 1
- no fabrication; if unsure, lower confidence and add data_gaps
""",
    tools=[get_sensor_context],
    output_key="pattern_analysis"
)
