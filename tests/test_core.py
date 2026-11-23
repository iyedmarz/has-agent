from has_agent.agent import extract_citations, parse_verification
from has_agent.chunking import clean_text, split_text
from has_agent.config import assert_local
from has_agent.textutils import reciprocal_rank_fusion, tokenize

import pytest


def test_clean_text_dehyphenates():
    assert clean_text("traite-\nment des patients") == "traitement des patients"


def test_split_text_respects_max_and_keeps_content():
    text = "\n\n".join(f"Paragraphe {i}. " + "mot " * 60 for i in range(10))
    chunks = split_text(text, max_chars=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)
    assert "Paragraphe 9" in chunks[-1]


def test_split_text_long_paragraph_terminates():
    chunks = split_text("Phrase courte. " * 500, max_chars=400, overlap=60)
    assert chunks and all(len(c) <= 400 for c in chunks)


def test_tokenize_strips_accents_and_stopwords():
    assert tokenize("Les médicaments de l'insuffisance rénale") == [
        "medicaments", "insuffisance", "renale",
    ]


def test_rrf_prefers_items_ranked_high_in_both_lists():
    scores = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]])
    ranked = sorted(scores, key=scores.get, reverse=True)
    assert set(ranked[:2]) == {"a", "b"}
    assert ranked[-1] in {"c", "d"}


def test_extract_citations_ignores_out_of_range():
    assert extract_citations("Vrai [1][3]. Faux [9] et [0].", 4) == [1, 3]


def test_parse_verification_handles_garbage():
    assert parse_verification('{"verdict": "supported", "unsupported_claims": []}') == (
        "supported", [],
    )
    assert parse_verification("not json") == ("unknown", [])


def test_assert_local_blocks_public_hosts():
    assert_local("http://127.0.0.1:11434")
    assert_local("http://localhost:11434")
    with pytest.raises(RuntimeError):
        assert_local("http://8.8.8.8:11434")
    with pytest.raises(RuntimeError):
        assert_local("https://api.example.com")
