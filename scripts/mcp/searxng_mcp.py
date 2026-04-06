#!/usr/bin/env python3
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from mcp.server.fastmcp import FastMCP

# -----------------------------------------------------------------------------
# Config (ENV-first)
# -----------------------------------------------------------------------------
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8080/search").strip()
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "12"))

# Default query behavior
DEFAULT_MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "8"))
DEFAULT_LANGUAGE = os.environ.get("LANGUAGE", "en")
DEFAULT_CATEGORIES = os.environ.get("CATEGORIES", "general,it,dev")
DEFAULT_SAFESEARCH = int(os.environ.get("SAFESEARCH", "1"))  # 0 off, 1 moderate, 2 strict
DEFAULT_ENGINES = os.environ.get("ENGINES", "")              # optional: "google,duckduckgo,github"
DEFAULT_TIME_RANGE = os.environ.get("TIME_RANGE", "")        # optional: "day|week|month|year" if supported by your SearXNG

# Input safety
MAX_QUERY_CHARS = int(os.environ.get("MAX_QUERY_CHARS", "400"))
ALLOW_NEWLINES = os.environ.get("ALLOW_NEWLINES", "false").lower() in ("1", "true", "yes", "y")

# Rate limiting (anti-spam)
MIN_INTERVAL_MS = int(os.environ.get("MIN_INTERVAL_MS", "500"))  # e.g. 500ms => max 2 req/s per process

# Cache (TTL) to reduce load and speed up repeated requests
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "120"))  # 0 disables cache
CACHE_MAX_ITEMS = int(os.environ.get("CACHE_MAX_ITEMS", "128"))

# Output/debug
INCLUDE_RAW_DEFAULT = os.environ.get("INCLUDE_RAW_DEFAULT", "false").lower() in ("1", "true", "yes", "y")
RAW_MAX_BYTES = int(os.environ.get("RAW_MAX_BYTES", "50000"))

# HTTP headers
USER_AGENT = os.environ.get("USER_AGENT", "MCP-LocalSearch/1.1 (+https://local)")

mcp = FastMCP("LocalSearch")

# -----------------------------------------------------------------------------
# HTTP session with retry
# -----------------------------------------------------------------------------
def _make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.35,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s

SESSION = _make_session()

# -----------------------------------------------------------------------------
# Simple rate limiter (per-process)
# -----------------------------------------------------------------------------
_last_call_ts = 0.0

def _rate_limit() -> None:
    global _last_call_ts
    now = time.time()
    min_interval = MIN_INTERVAL_MS / 1000.0
    delta = now - _last_call_ts
    if delta < min_interval:
        time.sleep(min_interval - delta)
    _last_call_ts = time.time()

# -----------------------------------------------------------------------------
# TTL cache (per-process, in-memory)
# -----------------------------------------------------------------------------
@dataclass
class CacheEntry:
    ts: float
    value: str

_cache: Dict[str, CacheEntry] = {}

def _cache_key(params: Dict[str, Any]) -> str:
    # Stable JSON ordering for cache key
    return json.dumps(params, sort_keys=True, ensure_ascii=True)

def _cache_get(key: str) -> Optional[str]:
    if CACHE_TTL_SECONDS <= 0:
        return None
    ent = _cache.get(key)
    if not ent:
        return None
    if (time.time() - ent.ts) > CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return ent.value

def _cache_put(key: str, value: str) -> None:
    if CACHE_TTL_SECONDS <= 0:
        return
    # evict oldest if over max
    if len(_cache) >= CACHE_MAX_ITEMS:
        oldest_key = min(_cache.keys(), key=lambda k: _cache[k].ts)
        _cache.pop(oldest_key, None)
    _cache[key] = CacheEntry(ts=time.time(), value=value)

# -----------------------------------------------------------------------------
# Sanitization / safety
# -----------------------------------------------------------------------------
def _sanitize_query(q: str) -> str:
    if not isinstance(q, str):
        raise ValueError("query must be a string")
    q = q.strip()
    if not q:
        raise ValueError("query must be non-empty")

    if not ALLOW_NEWLINES:
        q = q.replace("\r", " ").replace("\n", " ")

    # Collapse whitespace
    q = re.sub(r"\s+", " ", q).strip()

    # Hard cap
    if len(q) > MAX_QUERY_CHARS:
        q = q[:MAX_QUERY_CHARS].rstrip()

    return q

def _is_safe_url(u: str) -> bool:
    if not u:
        return False
    try:
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            return False
        if not p.netloc:
            return False
        return True
    except Exception:
        return False

def _dedupe_by_url(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for r in results:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(r)
    return out

# -----------------------------------------------------------------------------
# Parsing and error classification
# -----------------------------------------------------------------------------
def _extract_results(data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in (data.get("results") or [])[: max(0, limit)]:
        url = (r.get("url") or "").strip()
        if not _is_safe_url(url):
            continue
        out.append(
            {
                "title": (r.get("title") or "").strip(),
                "url": url,
                "snippet": (r.get("content") or "").strip(),
                "engine": (r.get("engine") or "").strip(),
                "score": r.get("score"),
                "publishedDate": r.get("publishedDate") or r.get("published_date") or "",
            }
        )
    return _dedupe_by_url(out)

def _classify_requests_error(e: Exception) -> Tuple[str, str]:
    if isinstance(e, requests.Timeout):
        return "timeout", str(e)
    if isinstance(e, requests.ConnectionError):
        return "connection", str(e)
    if isinstance(e, requests.HTTPError):
        return "http_status", str(e)
    return "request_failed", str(e)

def _safe_raw_dump(data: Any) -> str:
    try:
        raw = json.dumps(data, ensure_ascii=True)
    except Exception:
        raw = str(data)
    if len(raw.encode("utf-8")) > RAW_MAX_BYTES:
        # trim safely to byte size
        b = raw.encode("utf-8")[:RAW_MAX_BYTES]
        return b.decode("utf-8", errors="replace") + "...(truncated)"
    return raw

# -----------------------------------------------------------------------------
# MCP tool
# -----------------------------------------------------------------------------
@mcp.tool()
def search_web(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    language: str = DEFAULT_LANGUAGE,
    categories: str = DEFAULT_CATEGORIES,
    safesearch: int = DEFAULT_SAFESEARCH,
    engines: str = DEFAULT_ENGINES,
    time_range: str = DEFAULT_TIME_RANGE,
    include_raw: bool = INCLUDE_RAW_DEFAULT,
) -> str:
    """
    Search the web using a local SearXNG instance.

    Use this tool when you need up-to-date information, current documentation,
    or to verify details that may have changed recently.

    Output (JSON string):
      {
        "status": "ok" | "error",
        "query": "...",
        "meta": {...},
        "results": [ {title,url,snippet,engine,score,publishedDate}, ... ],
        "raw": "..." (optional, truncated)
      }

    Practical search tips for AI:
      - Include product + version (e.g., "ComfyUI Flux2Scheduler node inputs v0.4").
      - Use quotes for exact errors (e.g., "mat1 and mat2 shapes cannot be multiplied").
      - Use site: filters (e.g., "site:github.com repo:comfyanonymous/ComfyUI Flux2").
      - Narrow by time_range when investigating recent changes (day/week).
    """
    t0 = time.time()

    # Normalize parameters
    q = _sanitize_query(query)

    mr = int(max_results)
    if mr < 1:
        mr = 1
    if mr > 20:
        mr = 20

    lang = (language or "en").strip()
    cats = (categories or "general").strip()
    engs = (engines or "").strip()
    tr = (time_range or "").strip()

    params: Dict[str, Any] = {
        "q": q,
        "format": "json",
        "language": lang,
        "categories": cats,
        "safesearch": int(safesearch),
    }
    if engs:
        params["engines"] = engs

    # Some SearXNG deployments support time_range. If unsupported, it will be ignored or error.
    # We include it only if provided.
    if tr:
        params["time_range"] = tr

    # Rate limit + cache
    key = _cache_key(params | {"max_results": mr, "include_raw": bool(include_raw)})
    cached = _cache_get(key)
    if cached is not None:
        return cached

    _rate_limit()

    # Perform request
    try:
        resp = SESSION.get(SEARXNG_URL, params=params, timeout=HTTP_TIMEOUT)

        # Parse JSON
        try:
            data = resp.json()
        except Exception:
            out = {
                "status": "error",
                "query": q,
                "meta": {
                    "base_url": SEARXNG_URL,
                    "request_params": params,
                    "elapsed_ms": int((time.time() - t0) * 1000),
                },
                "results": [],
                "error": "bad_json",
                "details": f"Non-JSON response (HTTP {resp.status_code})",
            }
            s = json.dumps(out, ensure_ascii=True)
            _cache_put(key, s)
            return s

        if resp.status_code >= 400:
            # Prefer server-provided error field if present
            server_err = data.get("error") if isinstance(data, dict) else None
            out = {
                "status": "error",
                "query": q,
                "meta": {
                    "base_url": SEARXNG_URL,
                    "request_params": params,
                    "elapsed_ms": int((time.time() - t0) * 1000),
                },
                "results": [],
                "error": "http_status",
                "details": f"SearXNG HTTP {resp.status_code}: {server_err or 'request failed'}",
            }
            if include_raw:
                out["raw"] = _safe_raw_dump(data)
            s = json.dumps(out, ensure_ascii=True)
            _cache_put(key, s)
            return s

        results = _extract_results(data, mr)

        out: Dict[str, Any] = {
            "status": "ok",
            "query": q,
            "meta": {
                "base_url": SEARXNG_URL,
                "request_params": params,
                "count": len(results),
                "elapsed_ms": int((time.time() - t0) * 1000),
                "note": "If you are done searching, keep queries narrow and use quoted error strings for best results.",
            },
            "results": results,
        }
        if include_raw:
            out["raw"] = _safe_raw_dump(data)

        s = json.dumps(out, ensure_ascii=True)
        _cache_put(key, s)
        return s

    except Exception as e:
        err_type, details = _classify_requests_error(e)
        out = {
            "status": "error",
            "query": q,
            "meta": {
                "base_url": SEARXNG_URL,
                "request_params": params,
                "elapsed_ms": int((time.time() - t0) * 1000),
            },
            "results": [],
            "error": err_type,
            "details": details,
        }
        s = json.dumps(out, ensure_ascii=True)
        _cache_put(key, s)
        return s


if __name__ == "__main__":
    mcp.run()
