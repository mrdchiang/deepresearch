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

# Optional but recommended if exposed beyond localhost
export DEEPRESEARCH_API_TOKEN="change-me"
export DEEPRESEARCH_CORS_ORIGINS="https://your-site.example"

# 3. Start
python server.py

# 4. Open http://localhost:5000
```

## Who Already Has This?

Deep research is not new — every major AI platform now has a version. Here's how they compare:

| Platform | Web Search | Internal Data | Multi-Agent | Citations | Open Source | 2nd Brain |
|---|---|---|---|---|---|---|
| **Microsoft Researcher** | ✓ Bing | ✓ M365 Graph (email, files, chats) | ✓ | ✓ | ✗ | ✗ |
| **ChatGPT Deep Research** | ✓ | ✓ Uploaded files | ✓ | ✓ | ✗ | ✗ |
| **Google Gemini Deep Research** | ✓ | ✓ Gmail, Drive, Sheets | ✓ | ✓ | ✗ | ✗ |
| **Perplexity Deep Research** | ✓ | ✗ | ✓ | ✓ (best) | ✗ | ✗ |
| **Claude** | ✗ (limited) | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Grok (xAI)** | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| **DeepResearch (this)** | ✓ DuckDuckGo | ✓ Obsidian vault + local files | ✓ | ✓ | ✓ MIT | ✓ Obsidian wiki |

**What makes this different:**
- **Not locked to one provider** — use OpenAI, DeepSeek, Groq, or any OpenAI-compatible API
- **Runs anywhere** — local machine, VPS, or as an MCP server inside Claude Desktop/ChatGPT
- **Your data stays with you** — no cloud dependency, no subscription
- **Obsidian 2nd brain** — research persists as interlinked wiki notes, searchable by other LLMs
- **Free web search** — DuckDuckGo, no API key needed

### AI Agent Harnesses That Can Already Do This

Open-source agent frameworks can also perform deep research — here's how they compare:

| Agent Harness | Multi-Agent | Research Skill | Cross-Provider | Citations | MCP | 2nd Brain |
|---|---|---|---|---|---|---|
| **Hermes Agent** (Nous) | ✓ delegate_task | ✗ (but composable) | ✓ | ✗ (manual) | ✗ | ✓ via Obsidian skill |
| **OpenCode** | ✓ Supervisor-Researcher | ✓ [opencode-deep-research](https://skillsmp.com/opencode-deep-research) | ✓ | ✓ | ✓ | ✗ |
| **Claude Code** (Anthropic) | ✓ subagents | ✗ (general-purpose) | ✗ Claude only | ✗ (manual) | ✗ | ✗ |
| **DeepResearch (this)** | ✓ 4-agent pipeline | ✓ Purpose-built | ✓ any LLM | ✓ automatic | ✓ MCP server | ✓ Obsidian wiki |

**Why build another one?** Hermes and OpenCode can compose research from general-purpose tools. DeepResearch is purpose-built for one thing — structured, iterative, cited research reports. Like the difference between `curl` (general HTTP) and a dedicated REST client.

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

## Security Notes

By default the server binds to `127.0.0.1` for local use. Do not expose it publicly without setting `DEEPRESEARCH_API_TOKEN`, restricting `DEEPRESEARCH_CORS_ORIGINS`, and running behind a production WSGI server/reverse proxy.

Useful environment variables:

| Variable | Default | Description |
|---|---|---|
| `DEEPRESEARCH_API_TOKEN` | empty | Optional bearer token required for research/result/vault endpoints when set |
| `DEEPRESEARCH_HOST` | `127.0.0.1` | Bind host. Use `0.0.0.0` only behind proper network controls |
| `DEEPRESEARCH_PORT` | `5000` | Flask port |
| `DEEPRESEARCH_CORS_ORIGINS` | localhost + GitHub Pages origin | Comma-separated allowed browser origins |
| `DEEPRESEARCH_RATE_LIMIT_PER_MINUTE` | `10` | Simple per-client start-request limit |
| `DEEPRESEARCH_MAX_DEPTH` | `4` | Maximum research iterations accepted by the API |
| `DEEPRESEARCH_SESSION_TTL_SECONDS` | `86400` | Cleanup TTL for completed/error sessions |
| `DEEPRESEARCH_MAX_SESSIONS` | `100` | In-memory session cap |

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
