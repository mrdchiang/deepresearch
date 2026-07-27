"""
LLM client — OpenAI-compatible API calls with retry logic.
"""

import json, time
from config import CONFIG, ExternalServiceError

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

    last_error = None
    for attempt in range(3):
        try:
            resp = http_requests.post(
                f"{cfg['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "0") or "0")
                time.sleep(retry_after or (2 ** attempt))
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except http_requests.exceptions.Timeout as e:
            last_error = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
        except http_requests.exceptions.RequestException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status and 500 <= status < 600 and attempt < 2:
                last_error = e
                time.sleep(2 ** attempt)
                continue
            raise ExternalServiceError(f"LLM request failed with status {status or 'unknown'}") from e
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise ExternalServiceError("LLM response was not in the expected format") from e

    raise ExternalServiceError("LLM request timed out or was rate limited") from last_error


def parse_llm_json(response: str, context: str) -> dict:
    """Parse JSON-mode output and return a useful internal error on failure."""
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"[LLM JSON ERROR] {context}: {e}")
        raise
    if not isinstance(data, dict):
        raise ExternalServiceError(f"{context} returned a non-object JSON response")
    return data
