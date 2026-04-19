import json
import sqlite3


def test_health_and_status(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    status = client.get("/api/status")
    assert status.status_code == 200
    payload = status.json()
    assert "Voice Core" in payload
    assert "System Control" in payload


def test_chat_post_and_rest_logs(client):
    resp = client.post("/api/chat", json={"text": "open vscode"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"

    action_logs = client.get("/api/action-logs")
    assert action_logs.status_code == 200
    assert isinstance(action_logs.json()["logs"], list)


def test_privacy_call_logs_knowledge_analytics(client):
    privacy = client.get("/api/privacy/logs")
    assert privacy.status_code == 200
    assert len(privacy.json()["logs"]) >= 1

    call_logs = client.get("/api/call-logs?limit=200")
    assert call_logs.status_code == 200
    assert len(call_logs.json()["logs"]) >= 1

    knowledge = client.get("/api/knowledge")
    assert knowledge.status_code == 200
    heuristics = knowledge.json()["heuristics"]
    assert isinstance(heuristics, list)
    assert heuristics[0]["query"] == "follow up email"

    analytics = client.get("/api/analytics/summary")
    assert analytics.status_code == 200
    data = analytics.json()
    assert data["metrics"]["pipeline_value"] == 5000
    assert len(data["top_clients"]) == 1
    assert len(data["heatmap"]) >= 1


def test_settings_get_put_validate_reset(client):
    current = client.get("/api/settings")
    assert current.status_code == 200
    settings = current.json()["settings"]
    assert settings["theme"] == "Dark"

    update_payload = {
        "settings": {
            "theme": "Light",
            "models": {"chat": "mistral"},
            "tts": {"engine": "piper"},
            "wake_word": {"keyword": "wolf"},
            "general": {"max_history": 25},
            "spotify": {"client_id": "id", "client_secret": "secret"},
        }
    }
    updated = client.put("/api/settings", json=update_payload)
    assert updated.status_code == 200
    body = updated.json()
    assert body["success"] is True
    assert "theme" in body["changed_keys"]

    validated = client.get("/api/settings/validate")
    assert validated.status_code == 200
    checks = validated.json()["checks"]
    assert checks["ollama"]["ok"] is True
    assert checks["spotify_credentials"]["ok"] is True

    reset = client.post("/api/settings/reset")
    assert reset.status_code == 200
    after_reset = client.get("/api/settings")
    assert after_reset.json()["settings"]["theme"] == "Dark"


def test_diagnostics_get_and_run(client):
    baseline = client.get("/api/diagnostics")
    assert baseline.status_code == 200
    diagnostics = baseline.json()["diagnostics"]
    assert len(diagnostics) >= 3

    single = client.post("/api/diagnostics/run", json={"key": "router_api"})
    assert single.status_code == 200
    assert single.json()["result"]["status"] in {"PASS", "FAIL"}

    all_run = client.post("/api/diagnostics/run", json={})
    assert all_run.status_code == 200
    assert len(all_run.json()["diagnostics"]) == len(diagnostics)


def test_media_state_control_and_local_stream(client, backend_state, tmp_path, monkeypatch):
    state = client.get("/api/media/state")
    assert state.status_code == 200
    assert "state" in state.json()

    play = client.post("/api/media/control", json={"action": "play", "query": "lofi"})
    assert play.status_code == 200
    assert play.json()["success"] is True

    song_file = tmp_path / "sample.mp3"
    song_file.write_bytes(b"ID3fake")
    backend_state.function_executor._local_map["song_1"] = str(song_file)

    stream = client.get("/api/media/local/song_1")
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("audio/")


def test_tasks_crud_and_execute(client):
    listed = client.get("/api/tasks")
    assert listed.status_code == 200
    initial_count = len(listed.json()["tasks"])

    created = client.post("/api/tasks", json={"title": "Prepare report", "description": "Compile KPI deck"})
    assert created.status_code == 200
    assert created.json()["success"] is True

    listed_after_create = client.get("/api/tasks").json()["tasks"]
    assert len(listed_after_create) == initial_count + 1
    task_id = listed_after_create[-1]["id"]

    edited = client.put(f"/api/tasks/{task_id}", json={"title": "Prepare report v2", "description": "Compile KPI deck + notes"})
    assert edited.status_code == 200
    assert edited.json()["success"] is True

    executed = client.post(f"/api/tasks/{task_id}/execute")
    assert executed.status_code == 200
    assert executed.json()["success"] is True

    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True


def test_proposals_list_and_file_serving(client, repo_root):
    doc_dir = repo_root / "data" / "documents" / "proposals"
    doc_dir.mkdir(parents=True, exist_ok=True)

    proposal_file = doc_dir / "integration_test_proposal.md"
    proposal_file.write_text("# Proposal\n\nThis is a test proposal.", encoding="utf-8")

    listing = client.get("/api/documents/proposals")
    assert listing.status_code == 200
    names = [p["name"] for p in listing.json()["proposals"]]
    assert proposal_file.name in names

    fetched = client.get(f"/api/documents/proposals/{proposal_file.name}")
    assert fetched.status_code == 200
    assert "test proposal" in fetched.text.lower()

    traversal = client.get("/api/documents/proposals/..%2Fsecrets.txt")
    assert traversal.status_code in {400, 404}