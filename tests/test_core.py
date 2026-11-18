import pandas as pd
from keycontacts.cleaning.pipeline import normalize
from keycontacts.search.baseline import ContactSearcher
from keycontacts.ml.evaluation import recall_at_k, reciprocal_rank


def test_normalize_email_and_preserve_id():
    f = normalize(pd.DataFrame({"WBS": ["001"], "FPC Email": [" TEST@Example.com "]}))
    assert f.loc[0, "WBS"] == "001"
    assert f.loc[0, "FPC Email"] == "test@example.com"


def test_search_deduplication():
    f = pd.DataFrame({"Project Description": ["impuestos colombia", "impuestos colombia"],
                      "FPC Email": ["a@example.com", "a@example.com"]})
    found = ContactSearcher(f).search("impuestos", 3)
    assert len(found) == 1
    assert found[0]["verified_responsibility"] is False


def test_metrics():
    assert recall_at_k([["a", "b"]], [{"b"}]) == 1
    assert reciprocal_rank([["a", "b"]], [{"b"}]) == 0.5
