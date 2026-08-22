from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from app.models import get_provider_timeout_seconds


knowledge_agent = LlmAgent(
    name="KnowledgeDiagnosticAgent",
    model=LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=get_provider_timeout_seconds()),
    instruction="""
You correlate device error codes with known failures using the provided input.

If error_code is missing or unknown, return "unknown" with low confidence.

Return JSON:
{
  "root_cause": "...",
  "recommended_part": "...",
  "confidence": 0.0,
  "rationale": "...",
  "assumptions": ["..."],
  "data_gaps": ["..."]
}

Rules:
- confidence must be between 0 and 1
- be explicit when mapping is weak or speculative
""",
    output_key="knowledge_analysis"
)
