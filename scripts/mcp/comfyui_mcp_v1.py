#!/usr/bin/env python3
import io
import json
import math
import os
import pathlib
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional, Tuple

from mcp.server.fastmcp import FastMCP

# -----------------------------------------------------------------------------
# Configuration (ENV-first)
# -----------------------------------------------------------------------------
COMFYUI_BASE_URL = os.environ.get("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
MODEL_NAME = os.environ.get("MODEL_NAME", "Juggernaut_XL_Lightning.safetensors")

HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "30"))          # seconds for any HTTP request
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "2"))           # polling interval
MAX_WAIT_SECONDS = int(os.environ.get("MAX_WAIT_SECONDS", "1800"))  # must cover slow generations (e.g. 2 minutes)

# Safety limits for VRAM: enforce max output pixels by scaling down while preserving aspect ratio
MAX_PIXELS = int(os.environ.get("MAX_PIXELS", "3500000"))           # e.g. 3.5 MP
ROUND_TO = int(os.environ.get("ROUND_TO", "8"))                     # SDXL latent-friendly, usually multiple of 8

# Output safety: restrict writes under OUTPUT_BASE
OUTPUT_BASE = os.environ.get("OUTPUT_BASE", ".")
DEFAULT_FILENAME_PREFIX = os.environ.get("DEFAULT_FILENAME_PREFIX", "Claude_Gen")

DEFAULT_NEGATIVE_PROMPT = os.environ.get(
    "DEFAULT_NEGATIVE_PROMPT",
    "bad quality, blurry, ugly, text, watermark, logo, signature, caption, subtitles, frame, border, "
    "jpeg artifacts, banding, posterization, dithering, halftone dots, stippling, moire, checkerboard artifacts, "
    "film grain, noise, oversharpening"
)

# Defaults tuned for SDXL Lightning
DEFAULT_WIDTH = int(os.environ.get("DEFAULT_WIDTH", "1024"))
DEFAULT_HEIGHT = int(os.environ.get("DEFAULT_HEIGHT", "1024"))
DEFAULT_STEPS = int(os.environ.get("DEFAULT_STEPS", "6"))           # Lightning: typically 4-6
DEFAULT_CFG = float(os.environ.get("DEFAULT_CFG", "2.0"))           # Lightning: typically 1.5-2.0
DEFAULT_SAMPLER = os.environ.get("DEFAULT_SAMPLER", "dpmpp_sde")
DEFAULT_SCHEDULER = os.environ.get("DEFAULT_SCHEDULER", "karras")
DEFAULT_DENOISE = float(os.environ.get("DEFAULT_DENOISE", "1.0"))
DEFAULT_BATCH_SIZE = int(os.environ.get("DEFAULT_BATCH_SIZE", "1"))

DEFAULT_WEBP_QUALITY = int(os.environ.get("DEFAULT_WEBP_QUALITY", "92"))

mcp = FastMCP("ComfyUI_Local")


# -----------------------------------------------------------------------------
# Helpers: HTTP
# -----------------------------------------------------------------------------
def http_get_json(path: str) -> Dict[str, Any]:
    req = urllib.request.Request(f"{COMFYUI_BASE_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def http_post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def http_get_bytes(path: str) -> bytes:
    req = urllib.request.Request(f"{COMFYUI_BASE_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.read()


# -----------------------------------------------------------------------------
# Helpers: Safe output paths
# -----------------------------------------------------------------------------
def _safe_join_under_base(base: str, subdir: str, filename: str) -> str:
    """
    Prevent path traversal by forcing the final path to be under OUTPUT_BASE.
    - base: OUTPUT_BASE absolute or relative.
    - subdir: user-provided output_dir (treated as relative to base).
    - filename: user-provided output_filename.
    """
    base_path = pathlib.Path(base).expanduser().resolve()

    # Treat output_dir as relative; strip leading slashes/backslashes to avoid absolute paths.
    subdir_norm = (subdir or "").replace("\\", "/").lstrip("/")
    # Prevent weird things like "//" or "./"
    subdir_path = pathlib.Path(subdir_norm)

    # Sanitize filename: keep basename only
    fname = pathlib.Path(filename or "").name
    if not fname:
        fname = "generated_image.png"

    final_path = (base_path / subdir_path / fname).resolve()

    # Enforce: final_path must be within base_path
    try:
        final_path.relative_to(base_path)
    except Exception:
        raise ValueError("Unsafe output path (path traversal or absolute path is not allowed).")

    return str(final_path)


# -----------------------------------------------------------------------------
# Helpers: Size validation (VRAM-safe)
# -----------------------------------------------------------------------------
def _ceil_to_multiple(x: int, m: int) -> int:
    return int(math.ceil(max(1, x) / m) * m)


def _limit_pixels_preserve_aspect(w: int, h: int, max_pixels: int) -> Tuple[int, int]:
    w = int(w)
    h = int(h)
    if w <= 0 or h <= 0:
        raise ValueError("width and height must be > 0")

    px = w * h
    if px <= max_pixels:
        return w, h

    scale = math.sqrt(max_pixels / float(px))
    w2 = max(1, int(w * scale))
    h2 = max(1, int(h * scale))
    return w2, h2


def _prepare_size(width: int, height: int) -> Tuple[int, int]:
    w, h = _limit_pixels_preserve_aspect(width, height, MAX_PIXELS)
    w = max(ROUND_TO, _ceil_to_multiple(w, ROUND_TO))
    h = max(ROUND_TO, _ceil_to_multiple(h, ROUND_TO))
    return w, h


# -----------------------------------------------------------------------------
# ComfyUI workflow + result extraction
# -----------------------------------------------------------------------------
def queue_prompt(workflow: Dict[str, Any]) -> Tuple[str, str]:
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": client_id}
    resp = http_post_json("/prompt", payload)
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI /prompt did not return prompt_id. Response: {resp}")
    return prompt_id, client_id


def get_history(prompt_id: str) -> Dict[str, Any]:
    return http_get_json(f"/history/{prompt_id}")


def get_image_bytes(filename: str, subfolder: str, folder_type: str) -> bytes:
    qs = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    return http_get_bytes(f"/view?{qs}")


def wait_for_first_image(prompt_id: str, max_wait_seconds: int) -> Dict[str, Any]:
    """
    Wait until ComfyUI history for prompt_id contains at least one image output.
    Returns the image info dict: {filename, subfolder, type, ...}
    """
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        hist = get_history(prompt_id)
        if prompt_id in hist:
            outputs = (hist[prompt_id].get("outputs") or {})
            for _, node_output in outputs.items():
                if isinstance(node_output, dict) and "images" in node_output and node_output["images"]:
                    return node_output["images"][0]
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"Timed out waiting for ComfyUI result (prompt_id={prompt_id}).")


def _maybe_convert_to_webp(image_bytes: bytes, out_path_webp: str, quality: int) -> None:
    """
    Convert bytes (usually PNG from ComfyUI /view) to WEBP locally.
    Requires Pillow installed.
    """
    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        raise RuntimeError("Pillow is required for WEBP output. Install: pip install pillow") from e

    im = Image.open(io.BytesIO(image_bytes))
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")

    os.makedirs(os.path.dirname(out_path_webp) or ".", exist_ok=True)
    im.save(out_path_webp, format="WEBP", quality=int(quality), method=6)


# -----------------------------------------------------------------------------
# MCP Tools
# -----------------------------------------------------------------------------
@mcp.tool()
def generate_image(
    prompt_text: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    cfg: float = DEFAULT_CFG,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = DEFAULT_DENOISE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = DEFAULT_FILENAME_PREFIX,
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",   # "png" or "webp"
    max_wait_seconds: int = MAX_WAIT_SECONDS
) -> str:
    """
    Generate an image using local ComfyUI (SDXL Lightning).

    Parameters:
      - prompt_text (str): English description.
      - negative_prompt (str): English negative prompt.
      - width/height (int): Requested resolution in px. Will be clamped by MAX_PIXELS and rounded to multiples of ROUND_TO.
      - steps (int): Lightning recommended 4-6 (but configurable).
      - cfg (float): Lightning recommended ~1.5-2.0.
      - sampler_name (str), scheduler (str), denoise (float).
      - seed (int|None): If None + randomize_seed=True -> strong random seed per call.
      - randomize_seed (bool): If True, ignore stable seeding and generate new seed each call.
      - filename_prefix (str): ComfyUI SaveImage prefix (still downloads via /view).
      - output_dir/output_filename: Saved under OUTPUT_BASE (path traversal blocked).
      - output_format: "png" or "webp" (webp uses Pillow locally).
      - max_wait_seconds: Must cover slow generations (e.g., 2 minutes -> use >= 180).

    Tip:
      After finishing your session, call unload_models() to free VRAM/RAM via ComfyUI /free.
    """
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text must be a non-empty string")

    steps = int(steps)
    if steps < 1:
        raise ValueError("steps must be >= 1")

    cfg = float(cfg)
    if cfg <= 0:
        raise ValueError("cfg must be > 0")

    denoise = float(denoise)
    if denoise <= 0 or denoise > 1.0:
        raise ValueError("denoise must be in (0, 1]")

    batch_size = int(batch_size)
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")

    # Seed handling: strong random by default
    if randomize_seed or seed is None:
        seed_value = secrets.randbits(63)
    else:
        seed_value = int(seed)

    # VRAM-safe size handling
    gen_w, gen_h = _prepare_size(int(width), int(height))

    # Build workflow (SDXL Lightning)
    workflow = {
        "4": {
            "inputs": {"ckpt_name": MODEL_NAME},
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {"width": gen_w, "height": gen_h, "batch_size": batch_size},
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {"text": prompt_text, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {"text": negative_prompt, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "3": {
            "inputs": {
                "seed": seed_value,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]},
            "class_type": "SaveImage",
        },
    }

    try:
        prompt_id, _client_id = queue_prompt(workflow)

        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        image_data = get_image_bytes(img_info["filename"], img_info.get("subfolder", ""), img_info.get("type", "output"))

        # Decide output filename
        fmt = (output_format or "png").strip().lower()
        if fmt not in ("png", "webp"):
            raise ValueError('output_format must be "png" or "webp"')

        if not output_filename:
            ts = int(time.time())
            safe_prefix = "".join(c for c in (filename_prefix or "gen") if c.isalnum() or c in ("-", "_"))[:40] or "gen"
            output_filename = f"{safe_prefix}_{prompt_id}_{ts}.png" if fmt == "png" else f"{safe_prefix}_{prompt_id}_{ts}.webp"

        # Enforce safe output path under OUTPUT_BASE
        out_path = _safe_join_under_base(OUTPUT_BASE, output_dir, output_filename)

        # Save
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        if fmt == "png":
            with open(out_path, "wb") as f:
                f.write(image_data)
        else:
            # Convert locally to WEBP
            _maybe_convert_to_webp(image_data, out_path, DEFAULT_WEBP_QUALITY)

        result = {
            "status": "ok",
            "prompt_id": prompt_id,
            "seed": seed_value,
            "model": MODEL_NAME,
            "requested_size": {"width": int(width), "height": int(height)},
            "generated_size": {"width": int(gen_w), "height": int(gen_h)},
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": denoise,
            "batch_size": batch_size,
            "output_path": out_path,
            "note": "After finishing your generation session, call unload_models() to free VRAM/RAM via ComfyUI /free.",
        }
        return json.dumps(result, ensure_ascii=True)

    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        err = {"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}
        return json.dumps(err, ensure_ascii=True)
    except TimeoutError as e:
        err = {"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}
        return json.dumps(err, ensure_ascii=True)
    except Exception as e:
        err = {"status": "error", "error": "unexpected", "details": str(e)}
        return json.dumps(err, ensure_ascii=True)


@mcp.tool()
def unload_models(unload_models: bool = True, free_memory: bool = True) -> str:
    """
    Call ComfyUI /free to unload models and/or free memory.

    Use this after finishing your generation session to free VRAM/RAM.

    Parameters:
      - unload_models: unload currently loaded models
      - free_memory: attempt to free memory
    """
    payload = {"unload_models": bool(unload_models), "free_memory": bool(free_memory)}
    try:
        resp = http_post_json("/free", payload)
        result = {"status": "ok", "action": "/free", "payload": payload, "response": resp if resp else "(empty)"}
        return json.dumps(result, ensure_ascii=True)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        err = {"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}
        return json.dumps(err, ensure_ascii=True)
    except Exception as e:
        err = {"status": "error", "error": "unexpected", "details": str(e)}
        return json.dumps(err, ensure_ascii=True)


if __name__ == "__main__":
    mcp.run()
