"""
Orchestrator — iterative research loop, session management, concurrency.
"""

import json, time, threading, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CONFIG, SESSION_LOCK, ACTIVE_RESEARCH_COUNT, ACTIVE_RESEARCH_CONDITION, ExternalServiceError, public_error
from agents import planner_agent, searcher_agent, analyst_agent, synthesizer_agent

# ============================================================
# ORCHESTRATOR — Iterative Research Loop
# ============================================================

class ResearchSession:
    """Tracks a single research session with live progress updates."""

    def __init__(self, session_id: str, question: str, depth: int = None):
        self.id = session_id
        self.question = question
        self.depth = depth or CONFIG["research"]["max_iterations"]
        self.created_at = time.time()
        self.updated_at = self.created_at
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
        self._lock = threading.RLock()

    def emit(self, event_type: str, data: dict):
        """Send progress update to all SSE listeners."""
        with self._lock:
            self.updated_at = time.time()
            self.progress.append({"type": event_type, "data": data, "time": self.updated_at})
            listeners = list(self._listeners)
        for queue in listeners:
            queue.append({"event": event_type, "data": json.dumps(data)})

    def add_listener(self, queue: list):
        with self._lock:
            self._listeners.append(queue)

    def remove_listener(self, queue: list):
        with self._lock:
            if queue in self._listeners:
                self._listeners.remove(queue)


# In-memory session store
SESSIONS: dict[str, ResearchSession] = {}


def cleanup_sessions():
    """Drop old sessions and cap total in-memory sessions. Also clean hung active sessions."""
    now = time.time()
    ttl = CONFIG["security"]["session_ttl_seconds"]
    active_timeout = CONFIG["security"]["active_session_timeout_seconds"]
    max_sessions = CONFIG["security"]["max_sessions"]
    with SESSION_LOCK:
        # Remove completed/error sessions past TTL
        expired = [
            sid for sid, session in SESSIONS.items()
            if ttl > 0
            and session.status in ("complete", "error")
            and now - session.updated_at > ttl
        ]
        # Also remove active sessions that hung (past active timeout)
        hung = [
            sid for sid, session in SESSIONS.items()
            if active_timeout > 0
            and session.status not in ("complete", "error")
            and now - session.updated_at > active_timeout
        ]
        for sid in expired + hung:
            SESSIONS.pop(sid, None)
        # Decrement ACTIVE_RESEARCH_COUNT for hung sessions (they won't self-cleanup)
        if hung:
            global ACTIVE_RESEARCH_COUNT
            ACTIVE_RESEARCH_COUNT = max(0, ACTIVE_RESEARCH_COUNT - len(hung))
            ACTIVE_RESEARCH_CONDITION.notify_all()

        if max_sessions > 0 and len(SESSIONS) > max_sessions:
            ordered = sorted(SESSIONS.items(), key=lambda item: item[1].updated_at)
            for sid, session in ordered[:len(SESSIONS) - max_sessions]:
                if session.status in ("complete", "error"):
                    SESSIONS.pop(sid, None)


def parse_depth(value) -> int:
    max_depth = CONFIG["security"]["max_depth"]
    default_depth = min(CONFIG["research"]["max_iterations"], max_depth)
    if value is None:
        return default_depth
    try:
        depth = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError("depth must be an integer") from e
    if depth < 1 or depth > max_depth:
        raise ValueError(f"depth must be between 1 and {max_depth}")
    return depth


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

            # Search sub-questions in parallel
            iter_findings = []
            with ThreadPoolExecutor(max_workers=min(len(sub_questions), 5)) as executor:
                future_to_sq = {executor.submit(searcher_agent, sq): sq for sq in sub_questions}
                for future in as_completed(future_to_sq):
                    sq = future_to_sq[future]
                    try:
                        finding = future.result()
                    except Exception as e:
                        finding = {
                            "sub_question": sq["question"],
                            "findings": [],
                            "quality_assessment": f"Search failed: {e}",
                            "missing_information": ["Search error"],
                        }
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
        # Inject real metadata — the LLM may overwrite it in the prompt
        report["research_metadata"] = session.metadata
        session.report = report
        session.status = "complete"
        session.emit("report_complete", report)
        session.emit("phase", {
            "phase": "complete",
            "message": "Research complete!",
        })

    except Exception as e:
        session.status = "error"
        session.error = public_error(e)
        session.emit("error", {"message": session.error})
        print(f"[RESEARCH ERROR] {type(e).__name__}: {e}")


