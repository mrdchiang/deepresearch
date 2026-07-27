#!/usr/bin/env python3
"""
DeepResearch — Tier 3 Multi-Agent Research System
Equivalent to Microsoft Researcher: decomposes questions, searches web,
iterates through findings, produces structured cited reports.

Plug-and-play: pip install -r requirements.txt && python server.py
"""

import json, os, re, time, threading, uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from ddgs import DDGS

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY", os.getenv("DEEPRESEARCH_API_KEY", "sk-placeholder")),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("DEEPRESEARCH_MODEL", "gpt-4o"),
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "search": {
        "max_results": 5,       # results per sub-question
        "region": "wt-wt",      # worldwide
        "safesearch": "moderate",
        "timeout": 15,
    },
    "research": {
        "max_iterations": 3,    # plan → search → analyze → repeat
        "min_findings": 5,      # minimum findings before synthesizing
        "max_sub_questions": 5,
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
    },
    "vault": {
        "path": os.getenv("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/Documents/Obsidian Vault")),
        "enabled": True,  # set False to disable vault saving
    },
}

# ============================================================
# LLM CLIENT
# ============================================================

try:
    import requests as http_requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def llm_call(system_prompt: str, user_prompt: str, temperature: float = None, json_mode: bool = False) -> str:
    """Call the configured LLM (OpenAI-compatible API)."""
    if not HAS_REQUESTS:
        raise RuntimeError("requests library required. Run: pip install requests")

    cfg = CONFIG["llm"]
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature if temperature is not None else cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = http_requests.post(
        f"{cfg['base_url']}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ============================================================
# WEB SEARCH ENGINE
# ============================================================

def web_search(query: str, max_results: int = None) -> list[dict]:
    """Search the web using DuckDuckGo and return structured results."""
    if max_results is None:
        max_results = CONFIG["search"]["max_results"]

    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(
                query,
                max_results=max_results,
                region=CONFIG["search"]["region"],
                safesearch=CONFIG["search"]["safesearch"],
                timelimit=None,
            ):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        print(f"[SEARCH] DuckDuckGo error: {e} — trying with reduced results")
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=3):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
        except Exception as e2:
            print(f"[SEARCH] Fallback also failed: {e2}")

    return results


# ============================================================
# MULTI-AGENT SYSTEM
# ============================================================

# ── Agent 1: PLANNER ───────────────────────────────────────

PLANNER_PROMPT = """You are a senior research planner. Your job is to decompose a complex research 
question into specific, answerable sub-questions that cover all important angles.

For each sub-question, provide a search query that would find the best information.

Rules:
- 3-5 sub-questions, each targeting a different aspect
- Sub-questions should be specific and searchable, not vague
- Search queries should use keywords likely to surface authoritative sources
- Cover: facts/data, context/background, opposing views, practical implications, future trends

Return valid JSON with this exact structure:
{
  "decomposition_strategy": "brief explanation of your approach",
  "sub_questions": [
    {
      "id": 1,
      "question": "specific sub-question?",
      "search_query": "optimized search keywords",
      "angle": "what aspect this covers"
    }
  ]
}"""


def planner_agent(question: str) -> dict:
    """Plan: decompose the research question into sub-questions."""
    user = f"Research question: {question}\n\nBreak this down into sub-questions."
    response = llm_call(PLANNER_PROMPT, user, temperature=0.2, json_mode=True)
    return json.loads(response)


# ── Agent 2: SEARCHER ──────────────────────────────────────

SEARCHER_PROMPT = """You are a research analyst specializing in fact extraction. 
Given web search results about a specific sub-question, extract the key facts, 
statistics, quotes, and insights. Be precise and always cite your source URL.

Rules:
- Extract 3-6 key findings, each with a source URL
- Include specific data points, dates, numbers when available
- Note any contradictions between sources
- Flag speculation vs. established facts
- If results are low quality, say so honestly

Return valid JSON:
{
  "sub_question": "the question being answered",
  "findings": [
    {
      "fact": "specific finding with context",
      "source_url": "https://...",
      "source_title": "title of source",
      "confidence": "high|medium|low",
      "type": "data_point|quote|analysis|opinion"
    }
  ],
  "quality_assessment": "brief assessment of result quality",
  "missing_information": ["what's still unknown"]
}"""


def searcher_agent(sub_question: dict) -> dict:
    """Search web for a sub-question and extract findings."""
    query = sub_question.get("search_query", sub_question["question"])
    search_results = web_search(query, max_results=CONFIG["search"]["max_results"])

    if not search_results:
        return {
            "sub_question": sub_question["question"],
            "findings": [],
            "quality_assessment": "No search results found",
            "missing_information": ["All sources unavailable"],
        }

    # Format search results for the LLM
    results_text = "\n\n---\n".join(
        f"SOURCE {i+1}: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(search_results)
    )

    user = f"""Sub-question: {sub_question['question']}
Angle: {sub_question.get('angle', 'general')}

Web search results:
{results_text}

Extract key findings from these results."""

    response = llm_call(SEARCHER_PROMPT, user, temperature=0.2, json_mode=True)
    return json.loads(response)


# ── Agent 3: ANALYST ───────────────────────────────────────

ANALYST_PROMPT = """You are a research quality analyst. Review all findings collected so far 
against the original research question and identify gaps, contradictions, and weak areas.

Rules:
- Check if the original question is fully answered
- Identify any important angles not covered
- Flag findings with low confidence or dubious sources
- Suggest follow-up searches for gaps
- Be honest: if the research is sufficient, say so

Return valid JSON:
{
  "coverage_score": 1-10,
  "answered_aspects": ["aspects covered"],
  "gaps": [
    {
      "gap": "what's missing",
      "importance": "critical|important|nice_to_have",
      "follow_up_query": "suggested search to fill this gap"
    }
  ],
  "contradictions": [
    {"finding_a": "...", "finding_b": "...", "resolution_note": "..."}
  ],
  "overall_assessment": "brief summary of research quality",
  "needs_more_research": true/false
}"""


def analyst_agent(question: str, all_findings: list[dict]) -> dict:
    """Analyze findings and identify gaps."""
    findings_text = json.dumps(all_findings, indent=2)

    user = f"""Original question: {question}

All findings collected so far:
{findings_text}

Review these findings and identify gaps."""

    response = llm_call(ANALYST_PROMPT, user, temperature=0.3, json_mode=True)
    return json.loads(response)


# ── Agent 4: SYNTHESIZER ───────────────────────────────────

SYNTHESIZER_PROMPT = """You are a senior research writer. Synthesize all findings into a 
comprehensive, well-structured report. This is the final deliverable.

Rules:
- Start with an executive summary (2-3 sentences)
- Organize into logical sections with headings
- Include specific data points with citations [Source: title]
- Use tables for comparative data
- Note areas of uncertainty
- End with key takeaways
- Be balanced and objective

Return valid JSON:
{
  "title": "report title",
  "executive_summary": "2-3 sentence overview",
  "sections": [
    {
      "heading": "Section Heading",
      "content": "paragraph text with [Source: name] citations",
      "subsections": [],
      "table": {
        "headers": ["col1", "col2"],
        "rows": [["val1", "val2"]]
      }
    }
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2"],
  "uncertainty_notes": ["areas of remaining uncertainty"],
  "sources": [
    {"title": "...", "url": "..."}
  ],
  "research_metadata": {
    "sub_questions_asked": 0,
    "total_findings": 0,
    "iterations": 0,
    "search_queries": []
  }
}"""


def synthesizer_agent(question: str, all_findings: list[dict], metadata: dict) -> dict:
    """Synthesize all findings into a final structured report."""
    findings_text = json.dumps(all_findings, indent=2)
    meta_text = json.dumps(metadata, indent=2)

    user = f"""Original research question: {question}

All findings from research:
{findings_text}

Research metadata:
{meta_text}

Synthesize everything into a comprehensive final report."""

    response = llm_call(SYNTHESIZER_PROMPT, user, temperature=0.4, json_mode=True)
    return json.loads(response)


# ============================================================
# ORCHESTRATOR — Iterative Research Loop
# ============================================================

class ResearchSession:
    """Tracks a single research session with live progress updates."""

    def __init__(self, session_id: str, question: str, depth: int = None):
        self.id = session_id
        self.question = question
        self.depth = depth or CONFIG["research"]["max_iterations"]
        self.status = "planning"
        self.progress = []
        self.findings = []
        self.report = None
        self.error = None
        self.metadata = {
            "sub_questions_asked": 0,
            "total_findings": 0,
            "iterations": 0,
            "search_queries": [],
        }
        self._listeners = []  # SSE listeners

    def emit(self, event_type: str, data: dict):
        """Send progress update to all SSE listeners."""
        self.progress.append({"type": event_type, "data": data, "time": time.time()})
        for queue in self._listeners:
            queue.append({"event": event_type, "data": json.dumps(data)})

    def add_listener(self, queue: list):
        self._listeners.append(queue)

    def remove_listener(self, queue: list):
        if queue in self._listeners:
            self._listeners.remove(queue)


# In-memory session store
SESSIONS: dict[str, ResearchSession] = {}


def run_research(session: ResearchSession):
    """Execute the full multi-agent research loop in a background thread."""
    try:
        # ═══ PHASE 1: PLAN ═══
        session.status = "planning"
        session.emit("phase", {"phase": "planning", "message": "Decomposing research question..."})

        plan = planner_agent(session.question)
        sub_questions = plan.get("sub_questions", [])
        session.metadata["decomposition_strategy"] = plan.get("decomposition_strategy", "")
        session.metadata["sub_questions_asked"] = len(sub_questions)

        session.emit("plan_complete", {
            "strategy": plan.get("decomposition_strategy", ""),
            "sub_questions": [sq["question"] for sq in sub_questions],
            "count": len(sub_questions),
        })

        # ═══ PHASE 2-3: ITERATIVE SEARCH + ANALYZE ═══
        all_findings = []

        for iteration in range(session.depth):
            session.status = f"searching_iteration_{iteration + 1}"
            session.metadata["iterations"] = iteration + 1
            session.emit("phase", {
                "phase": "searching",
                "iteration": iteration + 1,
                "total_iterations": session.depth,
                "message": f"Research iteration {iteration + 1}/{session.depth} — searching {len(sub_questions)} angles...",
            })

            # Search each sub-question
            iter_findings = []
            for i, sq in enumerate(sub_questions):
                session.emit("agent_status", {
                    "agent": "Searcher",
                    "status": "searching",
                    "current": i + 1,
                    "total": len(sub_questions),
                    "query": sq.get("search_query", sq["question"]),
                })

                finding = searcher_agent(sq)
                iter_findings.append(finding)
                session.metadata["search_queries"].append(sq.get("search_query", sq["question"]))

                facts_count = len(finding.get("findings", []))
                session.metadata["total_findings"] += facts_count
                session.emit("finding_complete", {
                    "sub_question": sq["question"],
                    "facts_found": facts_count,
                    "quality": finding.get("quality_assessment", ""),
                })

            all_findings.extend(iter_findings)
            session.findings = all_findings

            # Analyze for gaps
            session.status = f"analyzing_iteration_{iteration + 1}"
            session.emit("phase", {
                "phase": "analyzing",
                "iteration": iteration + 1,
                "message": "Analyzing findings for gaps and contradictions...",
            })

            analysis = analyst_agent(session.question, all_findings)
            session.emit("analysis_complete", {
                "coverage_score": analysis.get("coverage_score", 0),
                "needs_more": analysis.get("needs_more_research", False),
                "gaps": [g["gap"] for g in analysis.get("gaps", [])],
                "assessment": analysis.get("overall_assessment", ""),
            })

            # Check if we're done
            if not analysis.get("needs_more_research", False) or iteration == session.depth - 1:
                break

            # Create new sub-questions from gaps
            gaps = analysis.get("gaps", [])
            critical_gaps = [g for g in gaps if g.get("importance") == "critical"]
            important_gaps = [g for g in gaps if g.get("importance") == "important"]

            new_sqs = critical_gaps + important_gaps[:3]  # Max 3 more sub-questions
            sub_questions = [
                {
                    "id": i + 1,
                    "question": g["gap"],
                    "search_query": g.get("follow_up_query", g["gap"]),
                    "angle": f"gap_fill_{g.get('importance', 'unknown')}",
                }
                for i, g in enumerate(new_sqs)
            ]

            if not sub_questions:
                break

        # ═══ PHASE 4: SYNTHESIZE ═══
        session.status = "synthesizing"
        session.emit("phase", {
            "phase": "synthesizing",
            "message": "Synthesizing all findings into final report...",
        })

        report = synthesizer_agent(session.question, all_findings, session.metadata)
        session.report = report
        session.status = "complete"
        session.emit("report_complete", report)
        session.emit("phase", {
            "phase": "complete",
            "message": "Research complete!",
        })

    except Exception as e:
        session.status = "error"
        session.error = str(e)
        session.emit("error", {"message": str(e)})
        print(f"[RESEARCH ERROR] {e}")


# ============================================================
# 2ND BRAIN WIKI MODULE — Obsidian / LLM-Wiki Integration
# ============================================================

WIKI_FRONTMATTER_AGENT_PROMPT = """You are a knowledge architect. Given a research report, produce 
a structured 2nd-brain wiki decomposition suitable for Obsidian and LLM-navigable knowledge bases.

Rules:
- Create atomic, interlinked notes following the "Karpathy LLM Wiki" pattern
- One concept per note, connected via [[wikilinks]]
- Every note has YAML frontmatter: title, created, type, tags, sources
- Tags should be lowercase, hyphenated, and reusable across notes
- Link related concepts with [[wikilinks]] (minimum 2 per note)
- Extract key entities (people, organizations, products, technologies) as separate notes
- Extract key concepts as concept notes
- The main research query becomes a query note
- Source URLs from the report become immutable raw notes

Return valid JSON:
{
  "vault_updates": {
    "raw_sources": [
      {"filename": "research/YYYY-MM-DD-topic-slug.md", "content": "markdown with frontmatter"}
    ],
    "entities": [
      {"filename": "entity-name.md", "content": "markdown with frontmatter and [[wikilinks]]"}
    ],
    "concepts": [
      {"filename": "concept-name.md", "content": "markdown with frontmatter and [[wikilinks]]"}
    ],
    "queries": [
      {
        "filename": "research-query-slug.md",
        "content": "query note with full summary, findings, and citations"
      }
    ]
  },
  "index_entries": [
    {"section": "entities|concepts|queries|raw", "wikilink": "[[Note Name]]", "summary": "one-line"}
  ]
}"""


def report_to_wiki(report: dict, question: str, session_id: str) -> dict:
    """Convert a research report into a 2nd-brain wiki decomposition via LLM."""
    report_json = json.dumps(report, indent=2)

    user = f"""Original research question: {question}

Full research report:
{report_json}

Decompose this into an interlinked 2nd-brain wiki. Create atomic notes for:
- The original sources (raw/)
- Key entities mentioned (people, companies, products, technologies)  
- Key concepts and findings
- The main research query with full context

Use [[wikilinks]] between related notes (minimum 2 per note).
Tags should be reusable, lowercase-hyphenated categories."""

    response = llm_call(WIKI_FRONTMATTER_AGENT_PROMPT, user, temperature=0.3, json_mode=True)
    return json.loads(response)


def ensure_vault_structure(vault_path: str):
    """Create the wiki directory structure if it doesn't exist."""
    dirs = ["raw/research", "entities", "concepts", "comparisons", "queries"]
    for d in dirs:
        Path(vault_path, d).mkdir(parents=True, exist_ok=True)


def get_or_create_file(vault_path: str, filename: str, default_content: str = "") -> str:
    """Get existing file content or return default."""
    filepath = Path(vault_path, filename)
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return default_content


def save_wiki_note(vault_path: str, filename: str, content: str):
    """Save a wiki note, creating parent directories if needed."""
    filepath = Path(vault_path, filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")


def update_index(vault_path: str, entries: list[dict]):
    """Update index.md with new entries under their sections."""
    index_path = Path(vault_path, "index.md")
    current = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    if not current:
        current = "# Wiki Index\n\n> Content catalog. Every wiki page listed under its type.\n\n"

    date_str = datetime.now().strftime("%Y-%m-%d")
    additions = {"entities": [], "concepts": [], "comparisons": [], "queries": [], "raw": []}

    for entry in entries:
        section = entry.get("section", "concepts")
        if section in additions:
            additions[section].append(f"- {entry['wikilink']} — {entry['summary']}")

    new_lines = []
    for section, items in additions.items():
        if items:
            section_header = section.title()
            new_lines.append(f"\n## {section_header}\n*Updated: {date_str}*")
            for item in items:
                new_lines.append(item)

    if new_lines:
        updated = current.rstrip() + "\n" + "\n".join(new_lines) + "\n"
    else:
        updated = current

    index_path.write_text(updated, encoding="utf-8")


def append_log(vault_path: str, action: str, details: str):
    """Append an entry to log.md."""
    log_path = Path(vault_path, "log.md")
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{date_str}] {action}\n{details}\n"

    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        # Rotate if > 500 lines
        if len(content.splitlines()) > 500:
            year = datetime.now().year
            archive_name = f"log-{year}.md"
            Path(vault_path, archive_name).write_text(content, encoding="utf-8")
            content = f"# Wiki Log\n\n> Log rotated from {archive_name}\n"
        content += entry
    else:
        content = f"# Wiki Log\n\n> Chronological record of all wiki actions.\n{entry}"

    log_path.write_text(content, encoding="utf-8")


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)


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
    return jsonify({
        "status": "ok",
        "model": CONFIG["llm"]["model"],
        "sessions_active": len([s for s in SESSIONS.values() if s.status not in ("complete", "error")]),
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/api/research", methods=["POST"])
def start_research():
    """Start a new research session. Returns session_id for SSE connection."""
    data = request.get_json()
    question = data.get("question", "").strip()
    depth = data.get("depth", None)

    if not question:
        return jsonify({"error": "question is required"}), 400
    if len(question) < 10:
        return jsonify({"error": "question too short (min 10 chars)"}), 400
    if len(question) > 1000:
        return jsonify({"error": "question too long (max 1000 chars)"}), 400

    session_id = uuid.uuid4().hex[:12]
    session = ResearchSession(session_id, question, depth)
    SESSIONS[session_id] = session

    # Start research in background thread
    thread = threading.Thread(target=run_research, args=(session,), daemon=True)
    thread.start()

    return jsonify({
        "session_id": session_id,
        "status": "started",
        "stream_url": f"/api/research/{session_id}/stream",
    })


@app.route("/api/research/<session_id>/stream")
def stream_research(session_id: str):
    """SSE endpoint for live research progress."""
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
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    return jsonify({
        "session_id": session.id,
        "question": session.question,
        "status": session.status,
        "progress": session.progress,
        "findings_count": len(session.findings),
        "report": session.report,
        "metadata": session.metadata,
        "error": session.error,
    })


@app.route("/api/research/<session_id>/report.md", methods=["GET"])
def get_report_markdown(session_id: str):
    """Get the report as Markdown."""
    session = SESSIONS.get(session_id)
    if not session or not session.report:
        return jsonify({"error": "report not ready"}), 404

    md = report_to_markdown(session.report)
    return Response(md, mimetype="text/markdown")


@app.route("/api/research/<session_id>/save-to-vault", methods=["POST"])
def save_to_vault(session_id: str):
    """Save the research report to the 2nd-brain Obsidian vault as wiki notes."""
    if not CONFIG["vault"]["enabled"]:
        return jsonify({"error": "Vault saving is disabled. Set vault.enabled=True in CONFIG."}), 400

    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    if not session.report:
        return jsonify({"error": "report not ready yet"}), 400

    vault_path = CONFIG["vault"]["path"]
    vault_path = os.path.expanduser(vault_path)

    try:
        # Ensure vault structure exists
        ensure_vault_structure(vault_path)

        # Decompose report into wiki notes via LLM
        wiki_data = report_to_wiki(session.report, session.question, session_id)

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
            f"Question: {session.question}\n"
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
        return jsonify({"error": f"Failed to save to vault: {str(e)}"}), 500


@app.route("/api/vault/status", methods=["GET"])
def vault_status():
    """Check vault configuration and existence."""
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
