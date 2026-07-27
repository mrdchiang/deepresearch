# DeepResearch — Tier 3 Multi-Agent Research System

A plug-and-play open-source equivalent to **Microsoft Researcher** — decomposes complex questions, searches the web via multiple specialized AI agents, iterates to fill gaps, and produces structured, source-cited reports.

```
Planner → Searcher (parallel) → Analyst → [gap? search again] → Synthesizer → Report
```

## Quick Start

```bash
# 1. Clone & install
git clone <this-repo>
cd researcher-agent
pip install -r requirements.txt

# 2. Set your API key (any OpenAI-compatible provider works)
export OPENAI_API_KEY="sk-..."

# Optional: custom endpoint / model
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export DEEPRESEARCH_MODEL="deepseek-chat"

# 3. Start
python server.py

# 4. Open http://localhost:5000
```

## How It Works

### The 4-Agent Pipeline

| Agent | Role | Runs |
|---|---|---|
| **Planner** | Decomposes your question into 3-5 targeted sub-questions | Once |
| **Searcher** | Searches the web for each sub-question, extracts key facts with source URLs | Per sub-question, per iteration |
| **Analyst** | Reviews all findings, scores coverage, identifies gaps and contradictions | Per iteration |
| **Synthesizer** | Combines everything into a structured, cited report | Once, at the end |

### The Iterative Loop

1. **Plan** — LLM breaks your question into searchable sub-questions
2. **Search** — Parallel web search for each angle via DuckDuckGo (free, no API key)
3. **Analyze** — LLM reviews findings, scores coverage (1-10), finds gaps
4. **Repeat or Finish** — If gaps remain and iterations left, search again. Otherwise, synthesize.
5. **Synthesize** — Full report with executive summary, sections, tables, citations, takeaways

### Output

Every report includes:
- Executive summary
- Organized sections with [Source: ...] citations
- Data tables for comparative findings
- Key takeaways
- Areas of uncertainty
- Full source list with URLs
- Research metadata (iterations, sub-questions, findings count)

## Configuration

All via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | required | Your API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom endpoint (DeepSeek, Groq, etc.) |
| `DEEPRESEARCH_MODEL` | `gpt-4o` | Model to use |

Or edit `CONFIG` dict at the top of `server.py`.

## API

### `POST /api/research`
Start a research session.

```json
{
  "question": "What are the economic impacts of AI on software jobs?",
  "depth": 3
}
```

Returns: `{ "session_id": "...", "stream_url": "/api/research/{id}/stream" }`

### `GET /api/research/{id}/stream`
SSE stream with live progress. Events: `phase`, `plan_complete`, `agent_status`, `finding_complete`, `analysis_complete`, `report_complete`, `done`.

### `GET /api/research/{id}`
Full research result including the report JSON.

### `GET /api/research/{id}/report.md`
Download the report as Markdown.

## Deploy to GitHub Pages

The `index.html` works standalone — just update the server URL in the UI to point to wherever your `server.py` is running:

1. Host `index.html` on GitHub Pages
2. Run `server.py` on your machine (or a cheap VPS)
3. Set `OPENAI_API_KEY` on the server
4. Users access the HTML from anywhere, research runs on your server

## Requirements

- Python 3.11+
- 4 packages: `flask`, `flask-cors`, `ddgs`, `requests`
- DuckDuckGo search (free, no API key, built-in)
- Any OpenAI-compatible LLM API (bring your own key)

## License

MIT — use it, fork it, ship it.
