from fastapi.testclient import TestClient

from app.backend.main import app


def test_health_and_model_info():
    with TestClient(app) as client:
        health=client.get("/health")
        assert health.status_code==200
        info=client.get("/model/info")
        assert info.status_code==200
        assert info.json()["target"]=="next_distress_score"


def test_bad_prediction_payload_is_rejected():
    with TestClient(app) as client:
        response=client.post("/predict", json={"victim_id":"V1"})
        assert response.status_code==422
