"""
Tests for DeepResearch — mock-based, no API key needed.
Run: python -m pytest test_server.py -v
"""

import json, os, sys, tempfile, threading, time, uuid
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from config import CONFIG, SESSION_LOCK, ExternalServiceError, public_error
from orchestrator import ResearchSession, SESSIONS, cleanup_sessions, parse_depth
from vault import safe_vault_path, save_wiki_note, update_index, append_log, ensure_vault_structure
from agents import planner_agent, searcher_agent, analyst_agent, synthesizer_agent
from server import require_api_token, enforce_rate_limit

# ═══════════════════════════════════════════════════════════
# 1. Security: public_error() sanitization
# ═══════════════════════════════════════════════════════════

def test_public_error_hides_secrets():
    """Errors must never leak API keys, paths, or provider payloads."""
    assert "Research failed" in public_error(Exception("secret: sk-abc123"))
    assert "Check server logs" in public_error(RuntimeError("internal path C:\\Users\\David"))
    # ExternalServiceError is safe by design — messages are curated
    assert "upstream 503" in str(ExternalServiceError("upstream 503"))

def test_public_error_handles_json_error():
    """JSON decode errors get a specific message."""
    from json import JSONDecodeError
    msg = public_error(JSONDecodeError("msg", "doc", 0))
    assert "malformed" in msg.lower() or "model returned" in msg.lower()


# ═══════════════════════════════════════════════════════════
# 2. Security: Vault path safety
# ═══════════════════════════════════════════════════════════

def test_safe_vault_path_blocks_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        # Valid path
        p = safe_vault_path(tmp, "notes/test.md")
        assert p.suffix == ".md"

        # Traversal blocked
        with pytest.raises(ValueError):
            safe_vault_path(tmp, "../escape.md")

        # Non-.md blocked
        with pytest.raises(ValueError):
            safe_vault_path(tmp, "test.txt")

        # Null byte blocked
        with pytest.raises(ValueError):
            safe_vault_path(tmp, "test\x00.md")


def test_save_wiki_note_collision_policy():
    """save_wiki_note should append -2, -3 on collision, not overwrite."""
    with tempfile.TemporaryDirectory() as tmp:
        ensure_vault_structure(tmp)
        save_wiki_note(tmp, "concepts/first.md", "original")
        save_wiki_note(tmp, "concepts/first.md", "second")
        save_wiki_note(tmp, "concepts/first.md", "third")

        # Original preserved
        assert (Path(tmp) / "concepts/first.md").read_text() == "original"
        # Collision creates -2
        assert (Path(tmp) / "concepts/first-2.md").read_text() == "second"
        # Collision creates -3
        assert (Path(tmp) / "concepts/first-3.md").read_text() == "third"


def test_update_index_and_log_use_safe_path():
    """index.md and log.md must go through safe_vault_path()."""
    with tempfile.TemporaryDirectory() as tmp:
        ensure_vault_structure(tmp)
        update_index(tmp, [{"section": "concepts", "wikilink": "[[Test]]", "summary": "A test note"}])
        append_log(tmp, "test", "Test log entry")

        assert (Path(tmp) / "index.md").exists()
        assert (Path(tmp) / "log.md").exists()
        assert "[[Test]]" in (Path(tmp) / "index.md").read_text()
        assert "Test log entry" in (Path(tmp) / "log.md").read_text()


# ═══════════════════════════════════════════════════════════
# 3. Input validation
# ═══════════════════════════════════════════════════════════

def test_parse_depth_validates_bounds():
    assert parse_depth(1) == 1
    assert parse_depth(4) == 4
    assert parse_depth(None) <= CONFIG["security"]["max_depth"]

    with pytest.raises(ValueError):
        parse_depth(0)
    with pytest.raises(ValueError):
        parse_depth(999)


# ═══════════════════════════════════════════════════════════
# 4. Session management
# ═══════════════════════════════════════════════════════════

def test_cleanup_sessions_removes_expired():
    SESSIONS.clear()
    sid = "test-expired-01"
    session = ResearchSession(sid, "test question", depth=1)
    session.status = "complete"
    session.updated_at = 0  # way in the past
    SESSIONS[sid] = session

    cleanup_sessions()
    assert sid not in SESSIONS


def test_cleanup_sessions_removes_hung_active():
    SESSIONS.clear()
    sid = "test-hung-01"
    session = ResearchSession(sid, "test question", depth=1)
    session.status = "planning"
    session.updated_at = 0  # way in the past
    SESSIONS[sid] = session

    cleanup_sessions()
    assert sid not in SESSIONS


def test_cleanup_sessions_keeps_recent():
    SESSIONS.clear()
    sid = "test-recent-01"
    session = ResearchSession(sid, "test question", depth=1)
    session.status = "planning"
    session.updated_at = time.time()  # just now
    SESSIONS[sid] = session

    cleanup_sessions()
    assert sid in SESSIONS


# ═══════════════════════════════════════════════════════════
# 5. Agent pipeline with mocked LLM
# ═══════════════════════════════════════════════════════════

MOCK_PLANNER_RESPONSE = json.dumps({
    "decomposition_strategy": "test strategy",
    "sub_questions": [
        {"id": 1, "question": "Test Q1?", "search_query": "test query 1", "angle": "test angle"},
        {"id": 2, "question": "Test Q2?", "search_query": "test query 2", "angle": "test angle 2"},
        {"id": 3, "question": "Test Q3?", "search_query": "test query 3", "angle": "test angle 3"},
    ]
})

MOCK_SEARCHER_RESPONSE = json.dumps({
    "sub_question": "Test Q1?",
    "findings": [
        {"fact": "Important fact", "source_url": "https://example.com", "source_title": "Example", "confidence": "high", "type": "data_point"}
    ],
    "quality_assessment": "good",
    "missing_information": []
})

MOCK_ANALYST_RESPONSE = json.dumps({
    "coverage_score": 9,
    "answered_aspects": ["test"],
    "gaps": [],
    "contradictions": [],
    "overall_assessment": "complete",
    "needs_more_research": False
})

MOCK_SYNTHESIZER_RESPONSE = json.dumps({
    "title": "Test Report",
    "executive_summary": "Test summary.",
    "sections": [{"heading": "Section 1", "content": "Test content.", "subsections": [], "table": None}],
    "key_takeaways": ["Takeaway 1"],
    "uncertainty_notes": [],
    "sources": [{"title": "Source", "url": "https://example.com"}],
    "research_metadata": {"sub_questions_asked": 3, "total_findings": 5, "iterations": 1, "search_queries": []}
})


@patch("agents.llm_call")
def test_planner_agent_parses_valid_json(mock_llm):
    mock_llm.return_value = MOCK_PLANNER_RESPONSE
    result = planner_agent("Test question?")
    assert len(result["sub_questions"]) == 3
    assert result["sub_questions"][0]["question"] == "Test Q1?"


@patch("agents.llm_call")
@patch("agents.web_search")
def test_searcher_agent_parses_valid_json(mock_search, mock_llm):
    mock_search.return_value = [{"title": "Test", "url": "https://example.com", "snippet": "test"}]
    mock_llm.return_value = MOCK_SEARCHER_RESPONSE
    result = searcher_agent({"question": "Test Q1?", "search_query": "test", "angle": "test"})
    assert len(result["findings"]) == 1
    assert result["findings"][0]["fact"] == "Important fact"


@patch("agents.llm_call")
def test_analyst_agent_parses_valid_json(mock_llm):
    mock_llm.return_value = MOCK_ANALYST_RESPONSE
    result = analyst_agent("Test question?", [MOCK_SEARCHER_RESPONSE])
    assert result["coverage_score"] == 9
    assert result["needs_more_research"] is False


@patch("agents.llm_call")
def test_synthesizer_agent_parses_valid_json(mock_llm):
    mock_llm.return_value = MOCK_SYNTHESIZER_RESPONSE
    result = synthesizer_agent("Test?", [{"findings": []}], {})
    assert result["title"] == "Test Report"
    assert len(result["sections"]) == 1
    assert len(result["key_takeaways"]) == 1


# ═══════════════════════════════════════════════════════════
# 6. ResearchSession threading
# ═══════════════════════════════════════════════════════════

def test_research_session_concurrent_emit():
    """emit() should be thread-safe with concurrent listeners."""
    session = ResearchSession("test-thread-01", "test")

    errors = []
    def worker():
        try:
            queue = []
            session.add_listener(queue)
            for _ in range(50):
                session.emit("test_event", {"n": _})
            session.remove_listener(queue)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(session.progress) == 200  # 4 workers × 50 emits


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
