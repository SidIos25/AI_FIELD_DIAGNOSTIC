from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4


def create_service_ticket(
    summary: str,
    priority: str = "high",
    device: str = "unknown",
) -> Dict[str, str]:
    """Create a deterministic ticket payload compatible with escalation workflows."""
    normalized_priority = str(priority or "high").strip().lower()
    if normalized_priority not in {"low", "medium", "high", "critical"}:
        normalized_priority = "high"

    ticket_id = f"AUTO-{uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    return {
        "ticket_id": ticket_id,
        "status": "created",
        "priority": normalized_priority,
        "device": str(device or "unknown"),
        "summary": str(summary or ""),
        "created_at": created_at,
    }
