def test_ws_system_stream(client):
    with client.websocket_connect("/ws/system") as ws:
        payload = ws.receive_json()
        assert "cpu" in payload
        assert "ram" in payload
        assert "netUp" in payload
        assert "netDown" in payload


def test_ws_status_stream(client):
    with client.websocket_connect("/ws/status") as ws:
        payload = ws.receive_json()
        assert "Voice Core" in payload
        assert "System Control" in payload
        assert "Neural Sonic" in payload


def test_ws_diagnostics_stream(client):
    with client.websocket_connect("/ws/diagnostics") as ws:
        payload = ws.receive_json()
        assert "diagnostics" in payload
        assert isinstance(payload["diagnostics"], list)


def test_ws_chat_stream(client):
    with client.websocket_connect("/ws/chat") as ws:
        payload = ws.receive_json()
        assert "messages" in payload
        assert isinstance(payload["messages"], list)


def test_ws_media_stream(client):
    with client.websocket_connect("/ws/media") as ws:
        payload = ws.receive_json()
        assert "state" in payload
        assert "isPlaying" in payload["state"]


def test_ws_call_logs_stream(client):
    with client.websocket_connect("/ws/call-logs") as ws:
        payload = ws.receive_json()
        assert "logs" in payload
        assert isinstance(payload["logs"], list)


def test_ws_execution_stream(client):
    with client.websocket_connect("/ws/execution") as ws:
        payload = ws.receive_json()
        assert "events" in payload
        assert isinstance(payload["events"], list)


def test_ws_privacy_stream(client):
    with client.websocket_connect("/ws/privacy") as ws:
        payload = ws.receive_json()
        assert "logs" in payload
        assert isinstance(payload["logs"], list)


def test_ws_safety_accepts_messages(client):
    with client.websocket_connect("/ws/safety") as ws:
        ws.send_json({"id": "fake-confirmation", "approved": True})


def test_ws_clarification_accepts_messages(client):
    with client.websocket_connect("/ws/clarification") as ws:
        ws.send_json({"id": "fake-clarification", "result": {"success": True, "mode": "confirm"}})