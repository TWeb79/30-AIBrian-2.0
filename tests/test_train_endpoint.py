from fastapi.testclient import TestClient
import os

from api import app


def test_train_vocabulary_file_mode(monkeypatch):
    fake_content = "line one\nline two\n"
    # Write a temporary training file and point the endpoint to it via env var
    training_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "_tmp_trainingfile.md"))
    monkeypatch.setenv("TRAINING_FILE_PATH", training_path)
    try:
        with open(training_path, 'w', encoding='utf-8') as f:
            f.write(fake_content)

        client = TestClient(app)
        # Call synchronously (background=false) so the worker runs inline
        resp = client.post("/api/train_vocabulary?mode=file&batch_size=2&background=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ("started", "completed")
    finally:
        try:
            os.remove(training_path)
        except Exception:
            pass



def test_train_vocabulary_unsupported_mode():
    client = TestClient(app)
    resp = client.post("/api/train_vocabulary?mode=resume&batch_size=2&background=false")
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
