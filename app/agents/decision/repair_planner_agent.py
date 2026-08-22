from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from app.models import get_provider_timeout_seconds
from app.tools.get_inventory_status import get_inventory_status

planner_agent = LlmAgent(
    name="RepairPlannerAgent",
    model=LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=get_provider_timeout_seconds()),
    instruction="""
You create repair plans from the final diagnosis.

MUST:
- Call get_inventory_status(part) before recommending any replacement.

If inventory is unavailable, set escalation_needed to true and suggest safe alternatives if any.
If confidence is below 0.65 or root cause is uncertain, include follow_ups with concrete clarifying checks.

Return JSON:
{
  "steps": ["..."],
  "required_parts": ["..."],
  "inventory": {"part_name": 0},
  "proceed": true,
  "escalation_needed": false,
  "follow_ups": ["..."],
  "notes": "..."
}
""",
    tools=[get_inventory_status],
    output_key="repair_plan"
)
