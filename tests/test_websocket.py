import json


def test_websocket_connection_and_heartbeat(client):
    with client.websocket_connect("/ws") as websocket:
        # Send ping
        websocket.send_text(json.dumps({"type": "ping"}))
        # Receive pong
        data_text = websocket.receive_text()
        data = json.loads(data_text)
        assert data.get("type") == "pong"
