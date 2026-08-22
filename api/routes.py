import os
import secrets
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Annotated, Any, Dict, Optional
from pydantic import BaseModel, Field, constr
import logging
from services.workflow_runner import run_diagnostic_workflow
from app.security.guardrails import SecurityGuardrails, SecurityLevel

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = max(1, int(os.getenv("DIAGNOSTIC_RATE_LIMIT_WINDOW_SECONDS", "60")))
RATE_LIMIT_MAX_REQUESTS = max(1, int(os.getenv("DIAGNOSTIC_RATE_LIMIT_MAX_REQUESTS", "30")))
_REQUEST_TIMESTAMPS = defaultdict(list)

# Initialize security guardrails
security = SecurityGuardrails(level=SecurityLevel.STRICT)

router = APIRouter(
    prefix="",
    tags=["Diagnostics"],
    responses={
        500: {"description": "Internal server error"},
        422: {"description": "Validation error - invalid input parameters"},
        400: {"description": "Security validation failed"}
    }
)


DeviceStr = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=80)]
ErrorCodeStr = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=40)]
DescriptionStr = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=1000)]


class DiagnosticRequest(BaseModel):
    device: DeviceStr = Field(..., description="Device model or asset ID")
    error_code: ErrorCodeStr = Field(..., description="Error code")
    description: DescriptionStr = Field(..., description="Description of symptoms")


class DiagnosticResponse(BaseModel):
    result: Dict[str, Any] = Field(..., description="Diagnostic results with root cause and repair plan")


def require_diagnostic_api_key(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> None:
    """Authenticate requests to the diagnostic endpoint using a configured API key."""
    expected_key = os.getenv("DIAGNOSTIC_API_KEY")
    if not expected_key:
        logger.warning("DIAGNOSTIC_API_KEY is not configured")
        raise HTTPException(status_code=401, detail="Authentication required")

    if x_api_key is None or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Authentication required")


def check_diagnostic_rate_limit() -> None:
    """Allow a modest in-process rate limit for the diagnostic endpoint."""
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    requests = _REQUEST_TIMESTAMPS["/diagnose"]
    _REQUEST_TIMESTAMPS["/diagnose"] = [ts for ts in requests if ts >= window_start]

    if len(_REQUEST_TIMESTAMPS["/diagnose"]) >= RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - _REQUEST_TIMESTAMPS["/diagnose"][0])))
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please retry later.",
            headers={"Retry-After": str(retry_after)},
        )

    _REQUEST_TIMESTAMPS["/diagnose"].append(now)


@router.post("/diagnose", response_model=DiagnosticResponse, summary="Run Diagnostic")
async def diagnose(
    req: DiagnosticRequest,
    _auth: None = Depends(require_diagnostic_api_key),
) -> DiagnosticResponse:
    """Analyze equipment failures and generate repair recommendations."""
    device_name = str(req.device).strip()
    error_code = str(req.error_code).strip()
    logger.info("diagnose_request_start device=%s error_code=%s", device_name, error_code)

    try:
        check_diagnostic_rate_limit()
    except HTTPException:
        logger.warning("diagnose_rate_limit_rejected device=%s error_code=%s", device_name, error_code)
        raise

    # Step 1: Input validation and sanitization
    input_data = req.model_dump()
    is_valid, error_msg, sanitized_input = security.validate_and_sanitize_input(input_data)

    if not is_valid:
        security.log_security_event("INPUT_VALIDATION_FAILED", {
            "error": error_msg,
            "device": input_data.get("device")
        })
        logger.warning("diagnose_input_validation_failed device=%s error=%s", device_name, error_msg)
        raise HTTPException(status_code=400, detail=f"Input validation failed: {error_msg}")

    logger.info("diagnose_input_validated device=%s", device_name)

    # Step 2: Run diagnostic workflow with sanitized input
    try:
        result = await run_diagnostic_workflow(sanitized_input)
    except Exception as exc:
        logger.exception("diagnose_workflow_failed device=%s error_code=%s", device_name, error_code)
        raise HTTPException(status_code=500, detail="Diagnostic workflow failed") from exc

    # Step 3: Validate and sanitize output
    response_data = {"result": result}
    is_valid, sanitized_response, error_msg = security.validate_output(response_data)

    if not is_valid:
        security.log_security_event("OUTPUT_VALIDATION_FAILED", {
            "error": error_msg,
            "device": sanitized_input.get("device")
        })
        logger.error("diagnose_output_validation_failed device=%s error=%s", device_name, error_msg)
        raise HTTPException(status_code=500, detail="Output validation failed")

    logger.info("diagnose_request_complete device=%s error_code=%s", device_name, error_code)
    return DiagnosticResponse(result=sanitized_response["result"])