#!/usr/bin/env python3
"""
DeepResearch — Tier 3 Multi-Agent Research System
Equivalent to Microsoft Researcher: decomposes questions, searches web,
iterates through findings, produces structured cited reports.

Plug-and-play: pip install -r requirements.txt && python server.py
"""

import json, os, re, time, threading, uuid
from collections import deque
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from ddgs import DDGS


# Imports from module split
from config import CONFIG, SESSION_LOCK, ExternalServiceError, public_error
from config import RATE_LIMITS, ACTIVE_RESEARCH_COUNT, ACTIVE_RESEARCH_CONDITION
from orchestrator import ResearchSession, SESSIONS, cleanup_sessions, parse_depth, run_research
from vault import *
from llm_client import llm_call
from search import web_search
from agents import planner_agent, searcher_agent, analyst_agent, synthesizer_agent


# ── Auth & rate limiting (Flask-dependent, kept here) ──

def require_api_token():
    """Require a bearer token only when DEEPRESEARCH_API_TOKEN is configured."""
    expected = CONFIG["security"]["api_token"]
    if not expected:
        return None
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {expected}":
        return jsonify({"error": "unauthorized"}), 401
    return None


def enforce_rate_limit() -> bool:
    limit = CONFIG["security"]["rate_limit_per_minute"]
    if limit <= 0:
        return True
    now = time.time()
    client = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    with SESSION_LOCK:
        hits = RATE_LIMITS.setdefault(client, deque())
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
    return True


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, origins=CONFIG["server"]["cors_origins"])


@app.route("/")
def index():
    """Serve the landing page."""
    return send_from_directory(".", "index.html")


@app.route("/app")
def app_page():
    """Serve the research app UI."""
    return send_from_directory(".", "app.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    cleanup_sessions()
    with SESSION_LOCK:
        sessions_active = len([s for s in SESSIONS.values() if s.status not in ("complete", "error")])
    return jsonify({
        "status": "ok",
        "model": CONFIG["llm"]["model"],
        "sessions_active": sessions_active,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/api/research", methods=["POST"])
def start_research():
    """Start a new research session. Returns session_id for SSE connection."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    if not enforce_rate_limit():
        return jsonify({"error": "rate limit exceeded"}), 429

    cleanup_sessions()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400
    if len(question) < 10:
        return jsonify({"error": "question too short (min 10 chars)"}), 400
    max_question_chars = CONFIG["security"]["max_question_chars"]
    if len(question) > max_question_chars:
        return jsonify({"error": f"question too long (max {max_question_chars} chars)"}), 400
    try:
        depth = parse_depth(data.get("depth", None))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    session_id = uuid.uuid4().hex[:12]
    session = ResearchSession(session_id, question, depth)

    # Enforce max concurrent research
    max_concurrent = CONFIG["security"]["max_concurrent_research"]
    with ACTIVE_RESEARCH_CONDITION:
        cleanup_sessions()
        if max_concurrent > 0:
            while ACTIVE_RESEARCH_COUNT >= max_concurrent:
                ACTIVE_RESEARCH_CONDITION.wait(timeout=30)
                cleanup_sessions()
        if CONFIG["security"]["max_sessions"] > 0 and len(SESSIONS) >= CONFIG["security"]["max_sessions"]:
            return jsonify({"error": "server is at session capacity"}), 429
        SESSIONS[session_id] = session
        ACTIVE_RESEARCH_COUNT += 1

    # Start research in background thread with timeout enforcement
    def _run_with_cleanup():
        try:
            run_research(session)
        finally:
            with ACTIVE_RESEARCH_CONDITION:
                global ACTIVE_RESEARCH_COUNT
                ACTIVE_RESEARCH_COUNT -= 1
                ACTIVE_RESEARCH_CONDITION.notify_all()

    thread = threading.Thread(target=_run_with_cleanup, daemon=True)
    thread.start()

    return jsonify({
        "session_id": session_id,
        "status": "started",
        "stream_url": f"/api/research/{session_id}/stream",
    })


@app.route("/api/research/<session_id>/stream")
def stream_research(session_id: str):
    """SSE endpoint for live research progress."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    with SESSION_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    def generate():
        queue = []
        session.add_listener(queue)

        try:
            # Send initial state
            yield f"data: {json.dumps({'event': 'connected', 'data': {'session_id': session_id, 'status': session.status}})}\n\n"

            # Stream progress events
            while True:
                while queue:
                    msg = queue.pop(0)
                    yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"

                if session.status in ("complete", "error"):
                    # Flush remaining messages
                    while queue:
                        msg = queue.pop(0)
                        yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                    yield f"event: done\ndata: {json.dumps({'status': session.status})}\n\n"
                    break

                time.sleep(0.5)

        except GeneratorExit:
            pass
        finally:
            session.remove_listener(queue)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/research/<session_id>", methods=["GET"])
def get_research(session_id: str):
    """Get the full research result."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    with SESSION_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    with session._lock:
        progress = list(session.progress)
        findings_count = len(session.findings)
        report = session.report
        metadata = dict(session.metadata)
        error = session.error

    return jsonify({
        "session_id": session.id,
        "question": session.question,
        "status": session.status,
        "progress": progress,
        "findings_count": findings_count,
        "report": report,
        "metadata": metadata,
        "error": error,
    })


@app.route("/api/research/<session_id>/report.md", methods=["GET"])
def get_report_markdown(session_id: str):
    """Get the report as Markdown."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    with SESSION_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    with session._lock:
        report = session.report
    if not report:
        return jsonify({"error": "report not ready"}), 404

    md = report_to_markdown(report)
    return Response(md, mimetype="text/markdown")


@app.route("/api/research/<session_id>/save-to-vault", methods=["POST"])
def save_to_vault(session_id: str):
    """Save the research report to the 2nd-brain Obsidian vault as wiki notes."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    if not CONFIG["vault"]["enabled"]:
        return jsonify({"error": "Vault saving is disabled. Set vault.enabled=True in CONFIG."}), 400

    with SESSION_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    with session._lock:
        report = session.report
        question = session.question
    if not report:
        return jsonify({"error": "report not ready yet"}), 400

    vault_path = CONFIG["vault"]["path"]
    vault_path = os.path.expanduser(vault_path)

    try:
        # Ensure vault structure exists
        ensure_vault_structure(vault_path)

        # Decompose report into wiki notes via LLM
        wiki_data = report_to_wiki(report, question, session_id)

        files_created = []
        vault_updates = wiki_data.get("vault_updates", {})

        # Save raw sources
        for source in vault_updates.get("raw_sources", []):
            filename = f"raw/{source['filename']}"
            save_wiki_note(vault_path, filename, source["content"])
            files_created.append(filename)

        # Save entities
        for entity in vault_updates.get("entities", []):
            filename = f"entities/{entity['filename']}"
            save_wiki_note(vault_path, filename, entity["content"])
            files_created.append(filename)

        # Save concepts
        for concept in vault_updates.get("concepts", []):
            filename = f"concepts/{concept['filename']}"
            save_wiki_note(vault_path, filename, concept["content"])
            files_created.append(filename)

        # Save query
        for query in vault_updates.get("queries", []):
            filename = f"queries/{query['filename']}"
            save_wiki_note(vault_path, filename, query["content"])
            files_created.append(filename)

        # Update index and log
        index_entries = wiki_data.get("index_entries", [])
        if index_entries:
            update_index(vault_path, index_entries)

        append_log(
            vault_path,
            "research-save",
            f"Research session {session_id} saved to vault.\n"
            f"Question: {question}\n"
            f"Files created: {len(files_created)}\n"
            + "\n".join(f"- {f}" for f in files_created),
        )

        return jsonify({
            "status": "saved",
            "vault_path": vault_path,
            "files_created": files_created,
            "count": len(files_created),
        })

    except Exception as e:
        print(f"[VAULT ERROR] {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to save to vault. Check server logs for details."}), 500


@app.route("/api/vault/status", methods=["GET"])
def vault_status():
    """Check vault configuration and existence."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    vault_path = os.path.expanduser(CONFIG["vault"]["path"])
    exists = Path(vault_path).exists()
    return jsonify({
        "enabled": CONFIG["vault"]["enabled"],
        "path": vault_path,
        "exists": exists,
        "note_count": len(list(Path(vault_path).rglob("*.md"))) if exists else 0,
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current configuration (safe values only)."""
    return jsonify({
        "model": CONFIG["llm"]["model"],
        "base_url": CONFIG["llm"]["base_url"],
        "max_iterations": CONFIG["research"]["max_iterations"],
        "search_region": CONFIG["search"]["region"],
    })


# ============================================================
# REPORT FORMATTERS
# ============================================================

def report_to_markdown(report: dict) -> str:
    """Convert JSON report to clean Markdown."""
    md = []
    md.append(f"# {report.get('title', 'Research Report')}")
    md.append("")
    md.append(f"*Generated by DeepResearch — {datetime.now().strftime('%B %d, %Y')}*")
    md.append("")
    md.append("## Executive Summary")
    md.append(report.get("executive_summary", ""))
    md.append("")

    for section in report.get("sections", []):
        heading = section.get("heading", "Section")
        md.append(f"## {heading}")
        md.append(section.get("content", ""))
        md.append("")

        # Subsections
        for sub in section.get("subsections", []):
            md.append(f"### {sub.get('heading', '')}")
            md.append(sub.get("content", ""))
            md.append("")

        # Tables
        table = section.get("table")
        if table:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if headers and rows:
                md.append(f"| {' | '.join(headers)} |")
                md.append(f"|{'|'.join(['---' for _ in headers])}|")
                for row in rows:
                    md.append(f"| {' | '.join(str(c) for c in row)} |")
                md.append("")

    # Key Takeaways
    md.append("## Key Takeaways")
    for t in report.get("key_takeaways", []):
        md.append(f"- {t}")
    md.append("")

    # Uncertainty
    uncertainty = report.get("uncertainty_notes", [])
    if uncertainty:
        md.append("## Areas of Uncertainty")
        for u in uncertainty:
            md.append(f"- {u}")
        md.append("")

    # Sources
    sources = report.get("sources", [])
    if sources:
        md.append("## Sources")
        for i, s in enumerate(sources, 1):
            url = s.get("url", "")
            title = s.get("title", "")
            md.append(f"{i}. [{title}]({url})")
        md.append("")

    # Metadata
    meta = report.get("research_metadata", {})
    md.append("---")
    md.append(f"*Research conducted across {meta.get('iterations', '?')} iterations, "
              f"covering {meta.get('sub_questions_asked', '?')} sub-questions, "
              f"with {meta.get('total_findings', '?')} total findings.*")

    return "\n".join(md)


# ── Templates endpoint ──

from templates import list_templates, apply_template
from search import deep_read


@app.route("/api/templates", methods=["GET"])
def get_templates():
    """List all research templates."""
    return jsonify({"templates": list_templates()})


@app.route("/api/templates/apply", methods=["POST"])
def apply_template_endpoint():
    """Apply a template to a subject and return the expanded prompt."""
    data = request.get_json(silent=True) or {}
    template_id = data.get("template_id", "custom")
    subject = data.get("subject", "").strip()
    if not subject:
        return jsonify({"error": "subject is required"}), 400
    prompt = apply_template(template_id, subject)
    return jsonify({"prompt": prompt, "template_id": template_id})


@app.route("/api/deep-read", methods=["POST"])
def deep_read_endpoint():
    """Fetch and extract content from a URL."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400
    result = deep_read(url)
    return jsonify(result)


@app.route("/api/research/<session_id>/followup", methods=["POST"])
def followup_research(session_id: str):
    """Multi-turn: ask a follow-up question against existing research findings."""
    auth_error = require_api_token()
    if auth_error:
        return auth_error
    with SESSION_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    if not session.report:
        return jsonify({"error": "original research not yet complete"}), 400

    data = request.get_json(silent=True) or {}
    followup = data.get("question", "").strip()
    if len(followup) < 5:
        return jsonify({"error": "follow-up question too short"}), 400

    # Re-run analyst + synthesizer with follow-up context
    from agents import analyst_agent, synthesizer_agent

    session.emit("phase", {"phase": "followup", "message": f"Follow-up: {followup}"})

    # Add follow-up as a gap-fill analysis
    existing_findings = [{
        "sub_question": session.question,
        "findings": [{"fact": s.get("heading", ""), "source_url": u.get("url", ""),
                       "source_title": u.get("title", ""), "confidence": "high", "freshness": "current_year", "type": "analysis"}
                      for s in session.report.get("sections", [])
                      for u in session.report.get("sources", [])[:1]],
    }]

    analysis = analyst_agent(followup, existing_findings)
    session.emit("analysis_complete", {
        "coverage_score": analysis.get("coverage_score", 0),
        "needs_more": analysis.get("needs_more_research", False),
        "assessment": analysis.get("overall_assessment", ""),
    })

    # Synthesize follow-up
    combined_meta = {**session.metadata, "followup_question": followup}
    followup_report = synthesizer_agent(followup, existing_findings, combined_meta)
    followup_report["title"] = f"Follow-up: {followup}"
    session.emit("report_complete", followup_report)

    return jsonify({"status": "complete", "report": followup_report})


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  DeepResearch — Tier 3 Multi-Agent Research System")
    print("=" * 60)
    print(f"  Model: {CONFIG['llm']['model']}")
    print(f"  Endpoint: {CONFIG['llm']['base_url']}")
    print(f"  Max iterations: {CONFIG['research']['max_iterations']}")
    print(f"  Server: http://{CONFIG['server']['host']}:{CONFIG['server']['port']}")
    vault_path = os.path.expanduser(CONFIG['vault']['path'])
    vault_exists = Path(vault_path).exists()
    vault_status_str = "✓ found" if vault_exists else "⚠ not found (will auto-create)"
    print(f"  Vault: {vault_path} ({vault_status_str})")
    print("=" * 60)
    print()
    print("  Set env vars to configure:")
    print("    OPENAI_API_KEY       — your API key (required)")
    print("    OPENAI_BASE_URL      — custom endpoint (optional)")
    print("    DEEPRESEARCH_MODEL   — model name (default: gpt-4o)")
    print("    OBSIDIAN_VAULT_PATH  — path to Obsidian vault for 2nd-brain saves")
    print()

    app.run(
        host=CONFIG["server"]["host"],
        port=CONFIG["server"]["port"],
        debug=CONFIG["server"]["debug"],
    )
