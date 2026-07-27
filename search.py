"""
Web search engine — DuckDuckGo via ddgs library. Also local file search.
"""

import os, re
from pathlib import Path
from config import CONFIG
from ddgs import DDGS


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
                    "source_type": "web",
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
                        "source_type": "web",
                    })
        except Exception as e2:
            print(f"[SEARCH] Fallback also failed: {e2}")

    return results


def file_search(query: str, search_paths: list[str] = None, max_results: int = 10) -> list[dict]:
    """Search local files for relevant content. Returns structured results like web_search."""
    if search_paths is None:
        search_paths = [os.path.expanduser("~/Documents"), os.path.expanduser("~/Desktop")]
        vault_path = CONFIG.get("vault", {}).get("path", "")
        if vault_path:
            search_paths.append(os.path.expanduser(vault_path))

    results = []
    keywords = query.lower().split()

    for search_path in search_paths:
        sp = Path(search_path).expanduser()
        if not sp.exists():
            continue

        for filepath in sp.rglob("*"):
            if filepath.suffix.lower() not in (".md", ".txt", ".py", ".js", ".html", ".json", ".csv", ".yaml", ".yml", ".pdf"):
                continue
            if filepath.stat().st_size > 10_000_000:  # Skip files > 10MB
                continue
            if any(part.startswith(".") for part in filepath.parts):  # Skip hidden dirs
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")[:5000]
                score = sum(1 for kw in keywords if kw in content.lower())
                if score > 0:
                    results.append({
                        "title": str(filepath.relative_to(sp)),
                        "url": f"file://{filepath}",
                        "snippet": content[:500],
                        "source_type": "local",
                        "relevance_score": score,
                        "size_bytes": filepath.stat().st_size,
                    })
            except Exception:
                continue

        if len(results) >= max_results:
            break

    results.sort(key=lambda r: -r.get("relevance_score", 0))
    return results[:max_results]


def deep_read(url: str, max_chars: int = 10000) -> dict:
    """Fetch and extract readable content from a URL. Returns structured result."""
    try:
        import requests as http_requests
        resp = http_requests.get(url, timeout=15, headers={
            "User-Agent": "DeepResearch/1.0 (research bot; contact@example.com)"
        })
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")

        if "text/html" in content_type:
            # Extract readable text from HTML
            import re as _re
            html = resp.text
            # Strip scripts, styles, and tags
            html = _re.sub(r'<script[^>]*>.*?</script>', '', html, flags=_re.DOTALL | _re.IGNORECASE)
            html = _re.sub(r'<style[^>]*>.*?</style>', '', html, flags=_re.DOTALL | _re.IGNORECASE)
            html = _re.sub(r'<[^>]+>', ' ', html)
            html = _re.sub(r'\s+', ' ', html).strip()
            text = html[:max_chars]
        elif "text/plain" in content_type or "application/json" in content_type:
            text = resp.text[:max_chars]
        elif "application/pdf" in content_type:
            text = f"[PDF document: {len(resp.content)} bytes. Use /api/upload/pdf to extract text.]"
        else:
            text = f"[Unsupported content type: {content_type}]"

        return {
            "url": url,
            "content": text,
            "content_type": content_type,
            "status_code": resp.status_code,
            "length": len(text),
            "source_type": "deep_read",
        }
    except Exception as e:
        return {
            "url": url,
            "content": "",
            "error": str(e),
            "source_type": "deep_read",
        }
