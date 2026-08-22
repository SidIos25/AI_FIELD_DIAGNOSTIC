from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from app.models import get_provider_timeout_seconds
from app.tools.create_service_ticket import create_service_ticket

escalation_agent = LlmAgent(
    name="EscalationAgent",
    model=LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=get_provider_timeout_seconds()),
    instruction="""
Create escalation tickets only when repair cannot proceed.

Escalate if:
- escalation_needed is true, OR
- confidence < 0.4, OR
- required inventory is unavailable.

Priority policy:
- critical: confidence < 0.25 OR safety-risk language in rationale
- high: confidence >= 0.25 and < 0.4 OR one or more required parts unavailable
- medium: confidence >= 0.4 and < 0.55

If escalation is NOT needed, return:
{"escalation_needed": false, "reason": "..."}

If escalation IS needed, call create_service_ticket with a concise summary and return:
{"escalation_needed": true, "reason": "...", "ticket": {...}}
""",
    tools=[create_service_ticket],
    output_key="escalation_ticket"
)
