import json

from streamlit.testing.v1 import AppTest
import dataset_kb


def test_app_starts_and_switches_language(monkeypatch, tmp_path) -> None:
    # A tiny valid cache makes CI deterministic and prevents a 57 MB network
    # download. Dataset download/index construction is covered at deployment.
    index = {
        "examples": [
            {
                "doc_type": "bank_statement",
                "text": "account statement opening closing balance debit credit transaction",
                "source": "Bank Statement/test.jpg",
            }
        ]
    }
    (tmp_path / "dataset_index.json").write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setenv("DHANDIDI_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(dataset_kb, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(dataset_kb, "INDEX_FILE", tmp_path / "dataset_index.json")

    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert app.selectbox[0].value == "English"
    assert len(app.get("file_uploader")) == 1

    app.selectbox[0].set_value("हिन्दी").run()
    assert not app.exception
    assert app.selectbox[0].label == "🌐 अपनी भाषा चुनें"
