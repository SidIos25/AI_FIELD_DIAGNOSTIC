from fastapi.testclient import TestClient

from app.main import app
import api.routes as routes


def test_diagnose_success(monkeypatch):
    async def fake_run_diagnostic_workflow(payload):
        return {
            "final_response": {
                "status": "ok",
                "failure_type": "test",
            },
            "responses": ["ok"],
        }

    monkeypatch.setenv("DIAGNOSTIC_API_KEY", "test-key")
    monkeypatch.setattr(routes, "run_diagnostic_workflow", fake_run_diagnostic_workflow)

    client = TestClient(app)
    response = client.post(
        "/diagnose",
        json={
            "device": "TEST-UNIT-1",
            "error_code": "E-TEST",
            "description": "Test description",
        },
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "final_response" in data["result"]
    assert data["result"]["final_response"]["status"] == "ok"


def test_diagnose_validation_error(monkeypatch):
    monkeypatch.setenv("DIAGNOSTIC_API_KEY", "test-key")
    client = TestClient(app)
    response = client.post(
        "/diagnose",
        json={"device": "X"},
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 422
