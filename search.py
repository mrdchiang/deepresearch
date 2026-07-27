"""
Web search engine — DuckDuckGo via ddgs library.
"""

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
