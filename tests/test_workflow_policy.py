import asyncio

import httpx
import openai

from google.adk.models.lite_llm import LiteLlm

import app.models as app_models
import app.rag.embeddings as embeddings_module
from services.workflow_runner import (
    _classify_dependency_error,
    _merge_agent_outputs,
    _merge_agent_outputs_with_validation,
    _run_agent_once,
    run_diagnostic_workflow,
)


def test_merge_outputs_adds_follow_up_for_low_confidence():
    responses = [
        '{"root_cause": "bearing wear", "confidence": 0.58, "required_parts": ["bearing_unit"], "inventory": {"bearing_unit": 3}}'
    ]

    merged = _merge_agent_outputs(responses)

    assert merged is not None
    assert merged["needs_follow_up"] is True
    assert isinstance(merged.get("follow_ups"), list)
    assert len(merged["follow_ups"]) > 0
    assert merged["escalation_needed"] is False
    assert merged["proceed"] is False


def test_merge_outputs_escalates_when_confidence_is_very_low():
    responses = [
        '{"root_cause": "insufficient_data", "confidence": 0.31, "required_parts": ["cooling_fan"], "inventory": {"cooling_fan": 5}}'
    ]

    merged = _merge_agent_outputs(responses)

    assert merged is not None
    assert merged["escalation_needed"] is True
    assert "low diagnostic confidence" in merged["reason"].lower()


def test_merge_outputs_escalates_when_required_parts_are_missing():
    responses = [
        '{"root_cause": "fan failure", "confidence": 0.9, "required_parts": ["cooling_fan", "imaginary_part"], "inventory": {"cooling_fan": 2, "imaginary_part": 0}}'
    ]

    merged = _merge_agent_outputs(responses)

    assert merged is not None
    assert merged["escalation_needed"] is True
    assert "imaginary_part" in merged["missing_parts"]
    assert merged["proceed"] is False


def test_merge_outputs_keeps_valid_data_and_flags_malformed_response():
    responses = [
        '{"root_cause": "bearing wear", "confidence": 0.92, "required_parts": ["bearing_unit"], "inventory": {"bearing_unit": 5}}',
        '{"root_cause": "this is malformed"'
    ]

    merged, malformed = _merge_agent_outputs_with_validation(responses)

    assert merged is not None
    assert merged["root_cause"] == "bearing wear"
    assert malformed
    assert malformed[0]["reason"] == "invalid_json"
    assert merged["proceed"] in {True, False}


def test_merge_outputs_rejects_non_dict_json():
    responses = [
        '["not", "an", "object"]',
        '{"root_cause": "bearing wear", "confidence": 0.9}'
    ]

    merged, malformed = _merge_agent_outputs_with_validation(responses)

    assert merged is not None
    assert any(item["reason"] == "non_dict_json" for item in malformed)


def test_merge_outputs_all_malformed_returns_structured_failure():
    responses = [
        '{"root_cause": "broken"',
        'not json at all',
        '[1, 2, 3]'
    ]

    merged, malformed = _merge_agent_outputs_with_validation(responses)

    assert merged is None
    assert len(malformed) == 3
    assert malformed[0]["reason"] == "invalid_json"
    assert malformed[1]["reason"] == "invalid_json"
    assert malformed[2]["reason"] == "non_dict_json"


def test_classify_dependency_error_for_missing_configuration():
    category, message = _classify_dependency_error(RuntimeError("OPENAI_KEY is not set"))

    assert category == "dependency_unavailable"
    assert "OPENAI_KEY" not in message
    assert "configured" in message.lower()


def test_run_agent_once_classifies_llm_timeout(monkeypatch):
    async def fake_inner(input_data):
        raise openai.APITimeoutError(
            httpx.Request("POST", "https://example.com/v1/chat/completions")
        )

    monkeypatch.setattr("services.workflow_runner._run_agent_once_inner", fake_inner)

    result = asyncio.run(_run_agent_once({"device": "test-device", "error_code": "E-100", "description": "fails"}))

    assert result["final_response"]["error"] == "llm_timeout"
    assert result["final_response"]["message"] == "The language model service timed out. Please retry."
    assert "Traceback" not in result["final_response"]["message"]
    assert "timed out" in result["final_response"]["message"].lower()


def test_run_agent_once_classifies_llm_provider_failure(monkeypatch):
    async def fake_inner(input_data):
        raise openai.APIConnectionError(
            message="provider unavailable",
            request=httpx.Request("POST", "https://example.com/v1/chat/completions"),
        )

    monkeypatch.setattr("services.workflow_runner._run_agent_once_inner", fake_inner)

    result = asyncio.run(_run_agent_once({"device": "test-device", "error_code": "E-101", "description": "fails"}))

    assert result["final_response"]["error"] == "llm_provider_error"
    assert "provider" in result["final_response"]["message"].lower()
    assert "unavailable" in result["final_response"]["message"].lower()
    assert "provider unavailable" not in result["final_response"]["message"].lower()


def test_run_diagnostic_workflow_marks_rag_unavailable(monkeypatch):
    async def fake_run_agent_once(input_data):
        return {"final_response": {"status": "ok"}, "responses": ["ok"]}

    def fake_retrieve_context(input_data):
        raise RuntimeError("ChromaDB unavailable")

    monkeypatch.setattr("services.workflow_runner.retrieve_context", fake_retrieve_context)
    monkeypatch.setattr("services.workflow_runner._run_agent_once", fake_run_agent_once)

    result = asyncio.run(run_diagnostic_workflow({"device": "test-device", "error_code": "E-200", "description": "test"}))

    assert result["final_response"]["status"] == "ok"
    assert result["final_response"]["rag"]["status"] == "unavailable"
    assert result["final_response"]["rag"]["error"] == "rag_unavailable"


def test_provider_timeout_default_is_configurable_and_safe(monkeypatch):
    monkeypatch.delenv("DIAGNOSTIC_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENAI_TIMEOUT_SECONDS", raising=False)

    assert app_models.get_provider_timeout_seconds() == 20.0


def test_provider_timeout_uses_environment_override(monkeypatch):
    monkeypatch.setenv("DIAGNOSTIC_TIMEOUT_SECONDS", "12.5")
    monkeypatch.delenv("OPENAI_TIMEOUT_SECONDS", raising=False)

    assert app_models.get_provider_timeout_seconds() == 12.5


def test_embedding_client_uses_configured_timeout(monkeypatch):
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setenv("DIAGNOSTIC_TIMEOUT_SECONDS", "7.5")
    monkeypatch.setattr(embeddings_module, "OpenAI", FakeOpenAI)
    embeddings_module._CLIENT = None

    client = embeddings_module._get_client()

    assert client.kwargs["timeout"] == 7.5


def test_litellm_accepts_configured_timeout(monkeypatch):
    monkeypatch.setenv("DIAGNOSTIC_TIMEOUT_SECONDS", "15")
    timeout_value = app_models.get_provider_timeout_seconds()

    model = LiteLlm("openai/gpt-4.1-mini", temperature=0.4, timeout=timeout_value)

    assert model is not None
    assert timeout_value == 15.0
