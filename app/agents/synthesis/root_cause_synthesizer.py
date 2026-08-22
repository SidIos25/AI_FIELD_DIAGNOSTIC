from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from app.models import get_provider_timeout_seconds

synthesizer_agent = LlmAgent(
    name="RootCauseSynthesizer",
    model=LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=get_provider_timeout_seconds()),
    instruction="""
You synthesize diagnostic evidence.

Inputs:
- pattern_analysis
- knowledge_analysis

Process:
- prefer higher-confidence evidence
- if analyses conflict, explain the conflict
- if both are low confidence (< 0.4), return "insufficient_data"

Return JSON:
{
  "root_cause": "...",
  "recommended_part": "...",
  "confidence": 0.0,
  "rationale": "...",
  "contradictions": ["..."],
  "follow_ups": ["..."]
}
""",
    output_key="final_diagnosis"
)
    