import os
from dotenv import load_dotenv
load_dotenv()

from google.adk.models.lite_llm import LiteLlm

DEFAULT_PROVIDER_TIMEOUT_SECONDS = 20.0


def get_provider_timeout_seconds() -> float:
    raw_value = os.getenv("DIAGNOSTIC_TIMEOUT_SECONDS", os.getenv("OPENAI_TIMEOUT_SECONDS", str(DEFAULT_PROVIDER_TIMEOUT_SECONDS)))
    try:
        timeout_seconds = float(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    if timeout_seconds <= 0:
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    return timeout_seconds


OPENAI_KEY = os.getenv("OPENAI_KEY")

OPENAI_MODEL = LiteLlm(
    model="openai/gpt-4.1-mini",
    temperature=0.4,
    api_key=OPENAI_KEY,
    timeout=get_provider_timeout_seconds(),
)
