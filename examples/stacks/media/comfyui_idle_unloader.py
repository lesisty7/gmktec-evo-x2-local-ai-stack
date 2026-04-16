#!/usr/bin/env python3
"""
ComfyUI Idle Unloader Sidecar

Polls ComfyUI /queue endpoint and calls /free when the queue has been idle
for IDLE_SECONDS, with a cooldown between free calls.

Environment variables:
  COMFYUI_BASE_URL      - ComfyUI HTTP address (default: http://comfyui:8188)
  IDLE_SECONDS          - Seconds of inactivity before /free (default: 900)
  POLL_SECONDS          - Polling interval (default: 15)
  FREE_COOLDOWN_SECONDS - Minimum seconds between /free calls (default: 300)
  STARTUP_WAIT_SECONDS  - Max wait for ComfyUI at startup (default: 600)
  HTTP_TIMEOUT          - HTTP request timeout in seconds (default: 5)
  FREE_UNLOAD_MODELS    - Pass unload_models=true to /free (default: true)
  FREE_MEMORY           - Pass free_memory=true to /free (default: true)
  LOG_MODE              - Logging verbosity: info | unload | quiet (default: info)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE_URL = os.environ.get("COMFYUI_BASE_URL", "http://comfyui:8188").rstrip("/")

IDLE_SECONDS = int(os.environ.get("IDLE_SECONDS", "900"))               # e.g. 300..1800
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "15"))                # e.g. 10..60
FREE_COOLDOWN_SECONDS = int(os.environ.get("FREE_COOLDOWN_SECONDS", "300"))

STARTUP_WAIT_SECONDS = int(os.environ.get("STARTUP_WAIT_SECONDS", "600"))  # max wait for /queue after sidecar startup
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "5"))

FREE_UNLOAD_MODELS = os.environ.get("FREE_UNLOAD_MODELS", "true").lower() in ("1", "true", "yes", "y")
FREE_MEMORY = os.environ.get("FREE_MEMORY", "true").lower() in ("1", "true", "yes", "y")

# LOG_MODE:
# - info   : start + activity + unload + warn + error
# - unload : only unload + error
# - quiet  : only error
LOG_MODE = os.environ.get("LOG_MODE", "info").strip().lower()
if LOG_MODE not in ("info", "unload", "quiet"):
    LOG_MODE = "info"


def _p(msg: str) -> None:
    print(msg, flush=True)


def log_info(msg: str) -> None:
    if LOG_MODE == "info":
        _p(msg)


def log_warn(msg: str) -> None:
    if LOG_MODE == "info":
        _p(msg)


def log_unload(msg: str) -> None:
    if LOG_MODE in ("info", "unload"):
        _p(msg)


def log_error(msg: str) -> None:
    _p(msg)


def http_get_json(path: str) -> dict:
    req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def http_post_json(path: str, payload: dict) -> int:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.getcode()


def is_busy(queue_info: dict) -> bool:
    running = queue_info.get("queue_running") or []
    pending = queue_info.get("queue_pending") or []
    return (len(running) > 0) or (len(pending) > 0)


def wait_for_comfyui() -> None:
    deadline = time.time() + STARTUP_WAIT_SECONDS
    attempt = 0

    log_info(f"[idle-unloader] BASE_URL={BASE_URL}")
    log_info(f"[idle-unloader] IDLE_SECONDS={IDLE_SECONDS} POLL_SECONDS={POLL_SECONDS} FREE_COOLDOWN_SECONDS={FREE_COOLDOWN_SECONDS}")
    log_info(f"[idle-unloader] STARTUP_WAIT_SECONDS={STARTUP_WAIT_SECONDS}")
    log_info(f"[idle-unloader] FREE_UNLOAD_MODELS={FREE_UNLOAD_MODELS} FREE_MEMORY={FREE_MEMORY}")
    log_info(f"[idle-unloader] LOG_MODE={LOG_MODE}")
    log_info(f"[idle-unloader] waiting for ComfyUI /queue (up to {STARTUP_WAIT_SECONDS}s)...")

    while time.time() < deadline:
        attempt += 1
        try:
            _ = http_get_json("/queue")
            log_info(f"[idle-unloader] ComfyUI is up (/queue ok) after {attempt} attempts")
            return
        except Exception as e:
            # do not spam – only in info mode, every 10 attempts
            if LOG_MODE == "info" and attempt % 10 == 0:
                log_warn(f"[idle-unloader] still waiting... last error: {e}")
            time.sleep(2)

    log_warn("[idle-unloader] WARN: ComfyUI not ready within STARTUP_WAIT_SECONDS; continuing with normal retries.")


def main() -> int:
    idle_since = None
    last_free_ts = 0.0

    wait_for_comfyui()

    while True:
        now = time.time()

        try:
            q = http_get_json("/queue")
            busy = is_busy(q)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            # in unload/quiet do not spam; ERROR is always printed
            if LOG_MODE == "info":
                log_warn(f"[idle-unloader] WARN: cannot read /queue ({e}); retrying...")
            time.sleep(POLL_SECONDS)
            continue
        except Exception as e:
            log_error(f"[idle-unloader] ERROR: unexpected error reading /queue ({e})")
            time.sleep(POLL_SECONDS)
            continue

        if busy:
            if idle_since is not None and LOG_MODE == "info":
                log_info("[idle-unloader] activity detected -> reset idle timer")
            idle_since = None
            time.sleep(POLL_SECONDS)
            continue

        # idle
        if idle_since is None:
            idle_since = now
            time.sleep(POLL_SECONDS)
            continue

        idle_for = now - idle_since
        cooldown_left = (last_free_ts + FREE_COOLDOWN_SECONDS) - now

        if idle_for >= IDLE_SECONDS and cooldown_left <= 0:
            payload = {
                "unload_models": bool(FREE_UNLOAD_MODELS),
                "free_memory": bool(FREE_MEMORY),
            }
            try:
                code = http_post_json("/free", payload)
                last_free_ts = now
                log_unload(f"[idle-unloader] /free -> {code} (idle_for={int(idle_for)}s) payload={payload}")
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                # errors are always shown
                log_error(f"[idle-unloader] ERROR: /free failed ({e})")
                last_free_ts = now  # anti-spam
            except Exception as e:
                log_error(f"[idle-unloader] ERROR: unexpected /free error ({e})")
                last_free_ts = now  # anti-spam

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
