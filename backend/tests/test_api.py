from fastapi.testclient import TestClient

from app.main import app
from tests.midi_factory import build_midi, chord_events

client = TestClient(app)


def upload(content: bytes, file_name: str = "song.mid"):
    return client.post("/api/analysis", files={"file": (file_name, content, "audio/midi")})


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analysis_returns_all_sections():
    data = build_midi(chord_events([60, 64, 67], 0, 2) + chord_events([55, 59, 62, 65], 2, 2))
    response = upload(data)

    assert response.status_code == 200
    body = response.json()
    assert body["file_name"] == "song.mid"
    assert body["duration_seconds"] == 2.0
    assert body["note_count"] == 7
    assert body["keys"]["overall"]["mode"] in ("major", "minor")  # key detection itself: test_key.py
    assert body["keys"]["segments"][0]["start"] == 0.0
    assert body["note_rate"]["peak_value"] == 4
    assert len(body["notes"]["pitch"]) == 7
    assert body["spectrum"]["frame_count"] > 0
    assert [c["name"] for c in body["chords"]] == ["C", "G7"]
    assert body["chords"][1]["notes"] == ["G3", "B3", "D4", "F4"]


def test_rejects_wrong_extension():
    response = upload(b"anything", file_name="song.mp3")
    assert response.status_code == 400


def test_rejects_invalid_midi():
    response = upload(b"not midi at all")
    assert response.status_code == 400
    assert "MIDI" in response.json()["detail"]
