"""
Security and guardrails layer for Field Diagnostic System.
Includes prompt injection detection, tool misuse protection, and output validation.
"""

import re
import json
from typing import Any, Dict, List, Set, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security enforcement levels."""
    STRICT = "strict"  # Block suspicious content
    MODERATE = "moderate"  # Log and allow with warnings
    PERMISSIVE = "permissive"  # Allow but log


class PromptInjectionDetector:
    """Detects potential prompt injection attempts in user inputs."""

    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        # Role override attempts
        (r"(?i)(ignore|disregard|forget).*previous", "role_override_attempt"),
        (r"(?i)you are now.*(?:system|admin|root)", "role_change_attempt"),
        (r"(?i)(system|admin)\s*prompt", "system_prompt_expose_attempt"),
        
        # Command injection - more specific (require execution context)
        (r"(?i)(?:execute|run)\s+(?:command|script|shell|system)", "command_execution_attempt"),
        (r"(?i)(?:rm\s+-rf|del\s+/s|chmod\s+777)", "destructive_command"),
        
        # Data extraction attempts
        (r"(?i)(?:reveal|show|expose|extract).*(?:password|key|secret|token)", "credential_extraction"),
        (r"(?i)(?:access|hack|breach).*(?:database|file|memory|system)", "unauthorized_access_attempt"),
        
        # Jailbreak patterns
        (r"(?i)(?:as an|pretend|imagine).*(?:evil|malicious|unethical)", "jailbreak_attempt"),
        (r"(?i)(?:DAN|dev mode|developer mode|test mode|bypass|unrestricted)", "jailbreak_mode"),
        
        # Multi-turn exploitation
        (r"(?i)(?:continue|forget|ignore).*(?:previous|instruction|rule)", "context_manipulation"),
    ]

    # Suspicious keywords threshold
    SUSPICIOUS_KEYWORDS = {
        "sql", "injection", "xss", "exploit", "vulnerability", "bypass",
        "override", "intercept", "decode", "encrypt", "leak", "exfiltrate"
    }

    def __init__(self, level: SecurityLevel = SecurityLevel.STRICT):
        self.level = level
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), name)
            for pattern, name in self.INJECTION_PATTERNS
        ]

    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect prompt injection attempts.
        
        Returns:
            Tuple of (is_injection_detected, list_of_detected_patterns)
        """
        if not isinstance(text, str) or len(text) == 0:
            return False, []

        detected_patterns = []
        
        # Check compiled patterns
        for pattern, name in self.compiled_patterns:
            if pattern.search(text):
                detected_patterns.append(name)
                logger.warning(f"Potential prompt injection detected: {name}")

        # Check for suspicious keyword concentration
        words_lower = text.lower()
        suspicious_count = sum(1 for keyword in self.SUSPICIOUS_KEYWORDS if keyword in words_lower)
        if suspicious_count >= 3:
            detected_patterns.append("high_keyword_concentration")
            logger.warning(f"High concentration of suspicious keywords: {suspicious_count}")

        return len(detected_patterns) > 0, detected_patterns

    def sanitize(self, text: str) -> str:
        """Remove/escape potentially dangerous content."""
        if not isinstance(text, str):
            return str(text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit input length (prevent token bomb)
        max_length = 5000
        if len(text) > max_length:
            logger.warning(f"Input truncated from {len(text)} to {max_length} chars")
            text = text[:max_length]
        
        return text.strip()


class ToolAccessControl:
    """Manages and validates tool access and usage."""

    def __init__(self):
        # Define allowed tools with their allowed parameters
        self.allowed_tools = {
            "get_sensor_context": {
                "params": {"device", "error_code"},
                "max_calls_per_session": 10,
                "rate_limit_per_minute": 20,
            },
            "get_inventory_status": {
                "params": {"part_name"},
                "max_calls_per_session": 15,
                "rate_limit_per_minute": 30,
            },
            "create_service_ticket": {
                "params": {"summary", "priority", "device"},
                "max_calls_per_session": 5,
                "rate_limit_per_minute": 10,
            },
        }
        
        # Track tool usage
        self.tool_call_count: Dict[str, int] = {}
        self.tool_timestamps: Dict[str, List[float]] = {}

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is in allowed list."""
        return tool_name in self.allowed_tools

    def validate_tool_params(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_tool_allowed(tool_name):
            return False, f"Tool '{tool_name}' is not allowed"

        allowed_params = self.allowed_tools[tool_name]["params"]
        provided_params = set(params.keys())

        # Check for unexpected parameters
        unexpected = provided_params - allowed_params
        if unexpected:
            return False, f"Unexpected parameters: {unexpected}"

        # Validate parameter values (basic type checking)
        for param_name, param_value in params.items():
            if param_value is None:
                return False, f"Parameter '{param_name}' cannot be None"
            
            if len(str(param_value)) > 500:
                return False, f"Parameter '{param_name}' exceeds max length"

        return True, None

    def check_rate_limit(self, tool_name: str, current_timestamp: float) -> Tuple[bool, Optional[str]]:
        """
        Check if tool call is within rate limits.
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not self.is_tool_allowed(tool_name):
            return False, f"Tool '{tool_name}' not found"

        config = self.allowed_tools[tool_name]
        
        # Update call count
        if tool_name not in self.tool_call_count:
            self.tool_call_count[tool_name] = 0
        
        self.tool_call_count[tool_name] += 1
        
        # Check session limit
        if self.tool_call_count[tool_name] > config["max_calls_per_session"]:
            return False, f"Tool '{tool_name}' session limit exceeded"

        # Check per-minute rate limit
        if tool_name not in self.tool_timestamps:
            self.tool_timestamps[tool_name] = []
        
        # Clean old timestamps (older than 1 minute)
        self.tool_timestamps[tool_name] = [
            ts for ts in self.tool_timestamps[tool_name]
            if current_timestamp - ts < 60
        ]
        
        if len(self.tool_timestamps[tool_name]) >= config["rate_limit_per_minute"]:
            return False, f"Tool '{tool_name}' rate limit exceeded"
        
        self.tool_timestamps[tool_name].append(current_timestamp)
        return True, None


class OutputValidator:
    """Validates and sanitizes model outputs before returning to users."""

    # Sensitive info patterns to redact
    SENSITIVE_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        (r'\b\d{16}\b', '[CREDIT_CARD]'),
        (r'(?i)(password|api_key|secret|token)\s*[:=]\s*[^\s]+', '[REDACTED]'),
    ]

    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.MULTILINE), replacement)
            for pattern, replacement in self.SENSITIVE_PATTERNS
        ]

    def validate_response_structure(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate that response has expected structure."""
        required_keys = {"result"}
        
        if not isinstance(response, dict):
            return False, "Response must be a dictionary"
        
        if not required_keys.issubset(response.keys()):
            return False, f"Response missing required keys: {required_keys - set(response.keys())}"
        
        result = response.get("result")
        if not isinstance(result, dict):
            return False, "Response 'result' must be a dictionary"
        
        return True, None

    def redact_sensitive_info(self, text: str) -> str:
        """Redact sensitive information from text."""
        if not isinstance(text, str):
            return text
        
        for pattern, replacement in self.compiled_patterns:
            text = pattern.sub(replacement, text)
        
        return text

    def sanitize_json_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize JSON response."""
        if isinstance(data, dict):
            return {
                key: self.sanitize_json_response(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.sanitize_json_response(item) for item in data]
        elif isinstance(data, str):
            return self.redact_sensitive_info(data)
        else:
            return data

    def validate_and_sanitize(self, response: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Full validation and sanitization pipeline.
        
        Returns:
            Tuple of (is_valid, sanitized_response, error_message)
        """
        # Validate structure
        is_valid, error = self.validate_response_structure(response)
        if not is_valid:
            return False, {}, error
        
        # Sanitize sensitive info
        sanitized = self.sanitize_json_response(response)
        
        # Validate JSON serializability
        try:
            json.dumps(sanitized)
        except (TypeError, ValueError) as e:
            return False, {}, f"Response not JSON serializable: {str(e)}"
        
        return True, sanitized, None


class InputValidator:
    """Validates and sanitizes user inputs."""

    def __init__(self, injection_detector: Optional[PromptInjectionDetector] = None):
        self.injection_detector = injection_detector or PromptInjectionDetector()

    def validate_device_field(self, device: str) -> Tuple[bool, Optional[str]]:
        """Validate device field."""
        if not isinstance(device, str) or not device.strip():
            return False, "Device must be a non-empty string"
        
        if len(device) > 80:
            return False, "Device name exceeds max length (80 chars)"
        
        # Allow alphanumeric, hyphens, underscores, spaces
        if not re.match(r'^[a-zA-Z0-9\-_\s]+$', device):
            return False, "Device contains invalid characters"
        
        return True, None

    def validate_error_code_field(self, error_code: str) -> Tuple[bool, Optional[str]]:
        """Validate error code field."""
        if not isinstance(error_code, str) or not error_code.strip():
            return False, "Error code must be a non-empty string"
        
        if len(error_code) > 40:
            return False, "Error code exceeds max length (40 chars)"
        
        # Allow alphanumeric and common error code symbols
        if not re.match(r'^[a-zA-Z0-9\-_:\.]+$', error_code):
            return False, "Error code contains invalid characters"
        
        return True, None

    def validate_description_field(self, description: str) -> Tuple[bool, Optional[str]]:
        """Validate description field."""
        if not isinstance(description, str):
            return False, "Description must be a string"
        
        if not description.strip():
            return False, "Description cannot be empty"
        
        if len(description) > 1000:
            return False, "Description exceeds max length (1000 chars)"
        
        # Check for prompt injection
        is_injection, patterns = self.injection_detector.detect(description)
        if is_injection:
            logger.warning(f"Potential injection in description: {patterns}")
            return False, f"Description contains suspicious patterns: {patterns}"
        
        return True, None

    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate and sanitize all input fields.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_input)
        """
        sanitized = {}
        
        # Validate device
        device = input_data.get("device")
        is_valid, error = self.validate_device_field(device)
        if not is_valid:
            return False, error, {}
        sanitized["device"] = self.injection_detector.sanitize(device)
        
        # Validate error_code
        error_code = input_data.get("error_code", "")
        is_valid, error = self.validate_error_code_field(error_code)
        if not is_valid:
            return False, error, {}
        sanitized["error_code"] = self.injection_detector.sanitize(error_code)
        
        # Validate description
        description = input_data.get("description")
        is_valid, error = self.validate_description_field(description)
        if not is_valid:
            return False, error, {}
        sanitized["description"] = self.injection_detector.sanitize(description)
        
        return True, None, sanitized


class SecurityGuardrails:
    """Main security guardrails orchestrator."""

    def __init__(self, level: SecurityLevel = SecurityLevel.STRICT):
        self.level = level
        self.injection_detector = PromptInjectionDetector(level)
        self.tool_access = ToolAccessControl()
        self.output_validator = OutputValidator()
        self.input_validator = InputValidator(self.injection_detector)

    def validate_and_sanitize_input(self, input_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate and sanitize user input."""
        return self.input_validator.validate_input(input_data)

    def check_tool_access(self, tool_name: str, params: Dict[str, Any], timestamp: float = None) -> Tuple[bool, Optional[str]]:
        """Check if tool can be accessed with given parameters."""
        import time
        timestamp = timestamp or time.time()
        
        # Check if tool is allowed
        is_valid, error = self.tool_access.validate_tool_params(tool_name, params)
        if not is_valid:
            logger.error(f"Tool validation failed for '{tool_name}': {error}")
            return False, error
        
        # Check rate limits
        is_allowed, error = self.tool_access.check_rate_limit(tool_name, timestamp)
        if not is_allowed:
            logger.error(f"Rate limit exceeded for tool '{tool_name}': {error}")
            return False, error
        
        return True, None

    def validate_output(self, response: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Validate and sanitize model output."""
        return self.output_validator.validate_and_sanitize(response)

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security-relevant events."""
        logger.info(f"SECURITY_EVENT: {event_type} - {details}")
