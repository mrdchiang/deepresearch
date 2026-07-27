"""
2nd Brain Wiki — Obsidian / LLM-Wiki integration for persistent research storage.
"""

import json, os, re
from pathlib import Path
from datetime import datetime
from config import CONFIG, ExternalServiceError
from llm_client import llm_call, parse_llm_json

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
    return parse_llm_json(response, "wiki")


def ensure_vault_structure(vault_path: str):
    """Create the wiki directory structure if it doesn't exist."""
    dirs = ["raw/research", "entities", "concepts", "comparisons", "queries"]
    for d in dirs:
        Path(vault_path, d).mkdir(parents=True, exist_ok=True)


def get_or_create_file(vault_path: str, filename: str, default_content: str = "") -> str:
    """Get existing file content or return default."""
    filepath = safe_vault_path(vault_path, filename)
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return default_content


def safe_vault_path(vault_path: str, filename: str) -> Path:
    """Resolve a note path and ensure it stays inside the configured vault."""
    if not filename or "\x00" in filename:
        raise ValueError("invalid wiki filename")
    normalized = filename.replace("\\", "/").lstrip("/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("../"):
        raise ValueError("wiki filename must be relative to the vault")
    vault_root = Path(vault_path).expanduser().resolve()
    filepath = (vault_root / normalized).resolve()
    if vault_root != filepath and vault_root not in filepath.parents:
        raise ValueError("wiki filename escapes the vault")
    if filepath.suffix.lower() != ".md":
        raise ValueError("wiki filename must end in .md")
    return filepath


def save_wiki_note(vault_path: str, filename: str, content: str):
    """Save a wiki note, creating parent directories. Adds suffix if file exists."""
    filepath = safe_vault_path(vault_path, filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # Collision policy: append -2, -3, etc. if file already exists
    if filepath.exists():
        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent
        counter = 2
        while filepath.exists():
            filepath = parent / f"{stem}-{counter}{suffix}"
            counter += 1
    filepath.write_text(content, encoding="utf-8")


def update_index(vault_path: str, entries: list[dict]):
    """Update index.md with new entries under their sections."""
    index_path = safe_vault_path(vault_path, "index.md")
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
    log_path = safe_vault_path(vault_path, "log.md")
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


