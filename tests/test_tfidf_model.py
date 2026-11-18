import pandas as pd
import pytest
from keycontacts.search.tfidf_model import LocalTfidfModel

@pytest.fixture
def model():
    frame = pd.DataFrame({
        "Project Description": ["taxes colombia finance", "network engineering germany", "taxes colombia"],
        "Customer Team": ["finance", "network", "finance"],
        "FPC Email": ["tax@example.com", "net@example.com", "tax@example.com"],
        "LM Email": [None, "lead@example.com", None],
    })
    return LocalTfidfModel.fit(frame)

def test_retrieves_and_deduplicates(model):
    r = model.predict("taxes colombia", top_k=3)
    assert len(r) == 1
    assert r[0]["contact"] == "tax@example.com"
    assert r[0]["verified_responsibility"] is False

def test_abstains_unknown_or_blank(model):
    assert model.predict("zzzzunknown") == []
    assert model.predict("  ") == []

def test_rejects_invalid_top(model):
    with pytest.raises(ValueError):
        model.predict("taxes", 0)

def test_save_load(tmp_path, model):
    destination = tmp_path / "tfidf.joblib"
    meta = model.save(destination)
    restored = LocalTfidfModel.load(destination)
    assert restored.predict("taxes colombia") == model.predict("taxes colombia")
    assert meta["rows"] == 3
    assert destination.with_suffix(".json").is_file()

def test_invalid_email_ignored():
    model = LocalTfidfModel.fit(pd.DataFrame({
        "Project Description": ["accounting"],
        "FPC Email": ["invalid-address"],
    }))
    assert model.predict("accounting") == []
