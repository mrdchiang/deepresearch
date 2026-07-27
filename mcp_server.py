#!/usr/bin/env python3
"""
DeepResearch MCP Server — plug into Claude Desktop, ChatGPT, Cursor, etc.
Usage: 
  python mcp_server.py                    # stdio mode (for Claude Desktop)
  python mcp_server.py --http             # HTTP mode with Flask UI (standalone)

One install, works everywhere.
"""

import json, os, re, sys, asyncio, uuid, threading
from pathlib import Path
from datetime import datetime

# Add parent to path so we can import server modules
sys.path.insert(0, str(Path(__file__).parent))

from server import (
    CONFIG, web_search, planner_agent, searcher_agent,
    analyst_agent, synthesizer_agent, report_to_markdown,
    report_to_wiki, ensure_vault_structure, save_wiki_note,
    update_index, append_log, llm_call,
    ExternalServiceError, public_error,
)

# ============================================================
# MCP SERVER
# ============================================================

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


mcp = Server("deepresearch")

# Track active research sessions
ACTIVE_RESEARCH: dict[str, dict] = {}


def run_research_sync(question: str, depth: int) -> dict:
    """Run the multi-agent research pipeline synchronously and return results."""
    session_id = uuid.uuid4().hex[:12]
    findings = []
    metadata = {
        "sub_questions_asked": 0,
        "total_findings": 0,
        "iterations": 0,
        "search_queries": [],
    }

    try:
        # Phase 1: Plan
        plan = planner_agent(question)
        sub_questions = plan.get("sub_questions", [])
        metadata["decomposition_strategy"] = plan.get("decomposition_strategy", "")
        metadata["sub_questions_asked"] = len(sub_questions)

        # Phase 2-3: Iterative search + analyze
        all_findings = []
        for iteration in range(depth):
            metadata["iterations"] = iteration + 1
            iter_findings = []
            for sq in sub_questions:
                finding = searcher_agent(sq)
                iter_findings.append(finding)
                metadata["search_queries"].append(sq.get("search_query", sq["question"]))
                metadata["total_findings"] += len(finding.get("findings", []))

            all_findings.extend(iter_findings)

            # Analyze
            if iteration < depth - 1:
                analysis = analyst_agent(question, all_findings)
                if not analysis.get("needs_more_research", False):
                    break
                gaps = analysis.get("gaps", [])
                critical_gaps = [g for g in gaps if g.get("importance") == "critical"]
                important_gaps = [g for g in gaps if g.get("importance") == "important"]
                new_sqs = critical_gaps + important_gaps[:3]
                if not new_sqs:
                    break
                sub_questions = [
                    {"id": i + 1, "question": g["gap"],
                     "search_query": g.get("follow_up_query", g["gap"]),
                     "angle": f"gap_fill_{g.get('importance', 'unknown')}"}
                    for i, g in enumerate(new_sqs)
                ]

        # Phase 4: Synthesize
        report = synthesizer_agent(question, all_findings, metadata)

        return {
            "session_id": session_id,
            "question": question,
            "report": report,
            "metadata": metadata,
            "markdown": report_to_markdown(report),
            "success": True,
        }

    except Exception as e:
        return {
            "session_id": session_id,
            "question": question,
            "error": public_error(e),
            "success": False,
        }


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="deep_research",
            description="Run a comprehensive multi-agent research pipeline on any question. "
                        "Uses Planner → Searcher → Analyst → Synthesizer agents to search the web, "
                        "analyze findings, identify gaps, and produce a structured cited report. "
                        "Best for complex questions requiring deep analysis.",
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The research question to investigate. Be specific and detailed.",
                        "minLength": 10,
                        "maxLength": 1000,
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Research depth: 1=quick, 2=standard, 3=deep (default), 4=exhaustive",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 4,
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="web_search",
            description="Quick web search returning structured results. Use for simple lookups "
                        "when full deep research isn't needed.",
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "minLength": 1,
                        "maxLength": 300,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="save_to_second_brain",
            description="Save research findings to your Obsidian vault as interlinked wiki notes "
                        "following the LLM-wiki / 2nd-brain pattern. Creates atomic notes with "
                        "frontmatter, [[wikilinks]], and auto-updates index/log.",
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Research content or report to save as wiki notes",
                        "minLength": 1,
                        "maxLength": 200000,
                    },
                    "topic": {
                        "type": "string",
                        "description": "Main topic/question for the wiki entry",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                },
                "required": ["content", "topic"],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "deep_research":
        question = str(arguments["question"]).strip()
        if len(question) < 10 or len(question) > 1000:
            return [TextContent(type="text", text="Research question must be 10-1000 characters.")]
        try:
            depth = parse_depth(arguments.get("depth", 3))
        except ValueError as e:
            return [TextContent(type="text", text=str(e))]

        result = await asyncio.to_thread(run_research_sync, question, depth)

        if not result["success"]:
            return [TextContent(
                type="text",
                text=f"❌ Research failed: {result['error']}"
            )]

        report = result["report"]
        meta = result["metadata"]

        # Build summary sections
        takeaways = "\n".join(f"- {t}" for t in report.get("key_takeaways", []))
        sections_text = "\n".join(
            f"## {s.get('heading', 'Section')}\n{s.get('content', '')[:500]}..."
            for s in report.get("sections", [])
        )
        sources_text = "\n".join(
            f"- [{s.get('title', 'Source')}]({s.get('url', '#')})"
            for s in report.get("sources", [])[:10]
        )

        summary = f"""## Research Complete: {report.get('title', question)}

**Executive Summary:** {report.get('executive_summary', '')}

**Research Stats:** {meta['iterations']} iterations · {meta['sub_questions_asked']} sub-questions · {meta['total_findings']} findings

---

### Key Takeaways
{takeaways}

---

### Full Report Sections
{sections_text}

### Sources ({len(report.get('sources', []))})
{sources_text}

---
*Full report available as Markdown below. Use save_to_second_brain to persist to Obsidian.*
"""

        return [
            TextContent(type="text", text=summary),
        ]

    elif name == "web_search":
        query = str(arguments["query"]).strip()
        max_results = max(1, min(int(arguments.get("max_results", 5)), 10))
        results = await asyncio.to_thread(web_search, query, max_results)

        if not results:
            return [TextContent(type="text", text="No results found.")]

        text = "\n\n".join(
            f"### [{r['title']}]({r['url']})\n{r['snippet']}"
            for r in results
        )
        return [TextContent(type="text", text=text)]

    elif name == "save_to_second_brain":
        content = str(arguments["content"])
        topic = str(arguments["topic"]).strip()

        vault_path = os.path.expanduser(CONFIG["vault"]["path"])

        if not CONFIG["vault"]["enabled"]:
            return [TextContent(
                type="text",
                text="❌ Vault saving is disabled. Set vault.enabled=True in server.py CONFIG."
            )]

        try:
            ensure_vault_structure(vault_path)

            # Create a simple wiki note for ad-hoc saves
            date_str = datetime.now().strftime("%Y-%m-%d")
            slug = re.sub(r"[^a-z0-9-]+", "-", topic.lower()).strip("-")[:60] or "research-note"

            # Create a query note
            note = f"""---
title: {json.dumps(topic)}
created: {date_str}
type: query
tags: [research, saved-from-mcp]
---

# {topic}

{content}

---
*Saved via DeepResearch MCP*
"""
            filename = f"queries/{date_str}-{slug}.md"
            save_wiki_note(vault_path, filename, note)

            # Update index + log
            update_index(vault_path, [{
                "section": "queries",
                "wikilink": f"[[{topic}]]",
                "summary": f"Saved on {date_str}"
            }])
            append_log(vault_path, "mcp-save", f"Saved query: {topic}")

            return [TextContent(
                type="text",
                text=f"✓ Saved to 2nd Brain!\nVault: {vault_path}\nNote: {filename}"
            )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Failed to save: {public_error(e)}"
            )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============================================================
# MAIN
# ============================================================

async def run_stdio():
    """Run in stdio mode for Claude Desktop / MCP clients."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DeepResearch MCP Server")
    parser.add_argument("--http", action="store_true", help="Run Flask HTTP server instead of stdio")
    args = parser.parse_args()

    if args.http:
        print("Starting DeepResearch HTTP server...")
        from server import app
        app.run(
            host=CONFIG["server"]["host"],
            port=CONFIG["server"]["port"],
            debug=False,
        )
    else:
        print("DeepResearch MCP Server starting (stdio mode)...", file=sys.stderr)
        asyncio.run(run_stdio())
