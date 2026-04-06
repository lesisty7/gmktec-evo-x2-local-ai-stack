#!/usr/bin/env python3
import io
import json
import math
import mimetypes
import os
import pathlib
import secrets
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional, Tuple

from mcp.server.fastmcp import FastMCP

COMFYUI_BASE_URL = os.environ.get("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
FLUX2_UNET = os.environ.get("FLUX2_UNET", "flux-2-klein-9b-Q5_K_M.gguf")
FLUX2_TEXT_ENCODER = os.environ.get("FLUX2_TEXT_ENCODER", "qwen_3_8b_fp4mixed.safetensors")
FLUX2_VAE = os.environ.get("FLUX2_VAE", "flux2-vae.safetensors")

HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "30"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "2"))
MAX_WAIT_SECONDS = int(os.environ.get("MAX_WAIT_SECONDS", "1800"))

MAX_PIXELS = int(os.environ.get("MAX_PIXELS", "3500000"))
ROUND_TO = int(os.environ.get("ROUND_TO", "16"))

OUTPUT_BASE = os.environ.get("OUTPUT_BASE", ".")
DEFAULT_FILENAME_PREFIX = os.environ.get("DEFAULT_FILENAME_PREFIX", "Flux2Klein9B_Gen")

DEFAULT_NEGATIVE_PROMPT = os.environ.get(
    "DEFAULT_NEGATIVE_PROMPT",
    "bad quality, blurry, ugly, text, watermark, logo, signature, caption, subtitles, frame, border, "
    "jpeg artifacts, banding, posterization, dithering, halftone dots, stippling, moire, checkerboard artifacts, "
    "film grain, noise, oversharpening"
)

DEFAULT_WIDTH = int(os.environ.get("DEFAULT_WIDTH", "768"))
DEFAULT_HEIGHT = int(os.environ.get("DEFAULT_HEIGHT", "768"))
DEFAULT_STEPS = int(os.environ.get("DEFAULT_STEPS", "4"))
DEFAULT_CFG = float(os.environ.get("DEFAULT_CFG", "3.0"))
DEFAULT_SAMPLER = os.environ.get("DEFAULT_SAMPLER", "euler")
DEFAULT_SCHEDULER = os.environ.get("DEFAULT_SCHEDULER", "flux2")
DEFAULT_DENOISE = float(os.environ.get("DEFAULT_DENOISE", "1.0"))
DEFAULT_BATCH_SIZE = int(os.environ.get("DEFAULT_BATCH_SIZE", "1"))
DEFAULT_WEBP_QUALITY = int(os.environ.get("DEFAULT_WEBP_QUALITY", "92"))
DEFAULT_UPSCALE_MODEL = os.environ.get("DEFAULT_UPSCALE_MODEL", "4x-UltraSharp.pth")

PRESET_PROFILES = {
    "fast": {"steps": 4, "cfg": 3.0},
    "balanced": {"steps": 6, "cfg": 3.2},
    "quality": {"steps": 8, "cfg": 3.4},
}

mcp = FastMCP("ComfyUI_Local_Flux2Klein9B")


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


def _safe_join_under_base(base: str, subdir: str, filename: str) -> str:
    base_path = pathlib.Path(base).expanduser().resolve()
    subdir_norm = (subdir or "").replace("\\", "/").lstrip("/")
    subdir_path = pathlib.Path(subdir_norm)
    fname = pathlib.Path(filename or "").name
    if not fname:
        fname = "generated_image.png"
    final_path = (base_path / subdir_path / fname).resolve()
    try:
        final_path.relative_to(base_path)
    except Exception as exc:
        raise ValueError("Unsafe output path (path traversal or absolute path is not allowed).") from exc
    return str(final_path)


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
    return max(1, int(w * scale)), max(1, int(h * scale))


def _prepare_size(width: int, height: int) -> Tuple[int, int]:
    w, h = _limit_pixels_preserve_aspect(width, height, MAX_PIXELS)
    w = max(ROUND_TO, _ceil_to_multiple(w, ROUND_TO))
    h = max(ROUND_TO, _ceil_to_multiple(h, ROUND_TO))
    return w, h


def _resolve_preset(preset: str, steps: Optional[int], cfg: Optional[float]) -> Tuple[int, float, str]:
    preset_name = (preset or "balanced").strip().lower()
    if preset_name not in PRESET_PROFILES:
        raise ValueError('preset must be one of: "fast", "balanced", "quality"')
    resolved_steps = PRESET_PROFILES[preset_name]["steps"] if steps is None else int(steps)
    resolved_cfg = PRESET_PROFILES[preset_name]["cfg"] if cfg is None else float(cfg)
    if resolved_steps < 1:
        raise ValueError("steps must be >= 1")
    if resolved_cfg <= 0:
        raise ValueError("cfg/guidance must be > 0")
    return resolved_steps, resolved_cfg, preset_name


def _compose_prompt(prompt_text: str, negative_prompt: str) -> str:
    prompt = (prompt_text or "").strip()
    if not prompt:
        raise ValueError("prompt_text must be a non-empty string")
    neg = (negative_prompt or "").strip()
    if not neg:
        return prompt
    if "avoid:" in prompt.lower():
        return prompt
    return f"{prompt}\nAvoid: {neg}"


def _infer_local_image_size(image_path: str) -> Tuple[int, int]:
    p = pathlib.Path(image_path).expanduser().resolve()
    with p.open("rb") as f:
        head = f.read(64)

        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", head[16:24])
            return int(width), int(height)

        if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
            if head[12:16] == b"VP8X":
                width_minus_one = int.from_bytes(head[24:27], "little")
                height_minus_one = int.from_bytes(head[27:30], "little")
                return width_minus_one + 1, height_minus_one + 1

        if head.startswith(b"\xff\xd8"):
            f.seek(2)
            while True:
                marker_prefix = f.read(1)
                if not marker_prefix:
                    break
                if marker_prefix != b"\xff":
                    continue
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                    _segment_len = struct.unpack(">H", f.read(2))[0]
                    _precision = f.read(1)
                    height, width = struct.unpack(">HH", f.read(4))
                    return int(width), int(height)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                segment_len_raw = f.read(2)
                if len(segment_len_raw) != 2:
                    break
                segment_len = struct.unpack(">H", segment_len_raw)[0]
                f.seek(max(0, segment_len - 2), os.SEEK_CUR)

    raise RuntimeError(f"Unsupported input image format for size inference: {p}")


def _build_multipart_formdata(fields: Dict[str, str], file_field: str, file_name: str, file_bytes: bytes, content_type: str) -> Tuple[bytes, str]:
    boundary = f"----codex{uuid.uuid4().hex}"
    body = io.BytesIO()
    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.write(str(value).encode("utf-8"))
        body.write(b"\r\n")
    body.write(f"--{boundary}\r\n".encode("utf-8"))
    body.write(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"\r\n'.encode("utf-8"))
    body.write(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.write(file_bytes)
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode("utf-8"))
    return body.getvalue(), boundary


def _upload_input_image(local_path: str, remote_name: Optional[str] = None) -> Dict[str, Any]:
    p = pathlib.Path(local_path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Input image not found: {p}")
    file_name = remote_name or f"codex_{uuid.uuid4().hex[:12]}_{p.name}"
    mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    payload, boundary = _build_multipart_formdata(
        fields={"type": "input", "overwrite": "true"},
        file_field="image",
        file_name=file_name,
        file_bytes=p.read_bytes(),
        content_type=mime_type,
    )
    req = urllib.request.Request(
        f"{COMFYUI_BASE_URL}/upload/image",
        data=payload,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if raw else {"name": file_name, "type": "input"}


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
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        hist = get_history(prompt_id)
        if prompt_id in hist:
            outputs = (hist[prompt_id].get("outputs") or {})
            for _, node_output in outputs.items():
                if isinstance(node_output, dict) and "images" in node_output and node_output["images"]:
                    return node_output["images"][0]
            status = (hist[prompt_id].get("status") or {}).get("status_str")
            if status in {"error", "failed"}:
                raise RuntimeError(json.dumps(hist[prompt_id], ensure_ascii=True))
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"Timed out waiting for ComfyUI result (prompt_id={prompt_id}).")


def _maybe_convert_to_webp(image_bytes: bytes, out_path_webp: str, quality: int) -> None:
    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        raise RuntimeError("Pillow is required for WEBP output. Install: pip install pillow") from e
    im = Image.open(io.BytesIO(image_bytes))
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
    os.makedirs(os.path.dirname(out_path_webp) or ".", exist_ok=True)
    im.save(out_path_webp, format="WEBP", quality=int(quality), method=6)


def _build_flux2_klein_t2i_workflow(
    prompt_text: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
    sampler_name: str,
    seed_value: int,
    batch_size: int,
    filename_prefix: str,
) -> Dict[str, Any]:
    return {
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX2_UNET}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX2_TEXT_ENCODER, "type": "flux2", "device": "default"}},
        "20": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": prompt_text}},
        "13": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["12", 0], "guidance": float(guidance)}},
        "14": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["13", 0]}},
        "15": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler_name}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed_value, "mode": "fixed"}},
        "17": {"class_type": "Flux2Scheduler", "inputs": {"steps": int(steps), "width": int(width), "height": int(height)}},
        "18": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": int(width), "height": int(height), "batch_size": int(batch_size)}},
        "19": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["14", 0], "sampler": ["15", 0], "sigmas": ["17", 0], "latent_image": ["18", 0]}},
        "21": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["20", 0]}},
        "22": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["21", 0]}},
    }


def _build_flux2_klein_i2i_workflow(
    prompt_text: str,
    input_image_name: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
    denoise: float,
    sampler_name: str,
    seed_value: int,
    filename_prefix: str,
) -> Dict[str, Any]:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_image_name}},
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX2_UNET}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX2_TEXT_ENCODER, "type": "flux2", "device": "default"}},
        "20": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "2": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["20", 0]}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": prompt_text}},
        "13": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["12", 0], "guidance": float(guidance)}},
        "14": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["13", 0]}},
        "15": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler_name}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed_value, "mode": "fixed"}},
        "17": {"class_type": "Flux2Scheduler", "inputs": {"steps": int(steps), "width": int(width), "height": int(height)}},
        "18": {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["17", 0], "denoise": float(denoise)}},
        "19": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["14", 0], "sampler": ["15", 0], "sigmas": ["18", 1], "latent_image": ["2", 0]}},
        "21": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["20", 0]}},
        "22": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["21", 0]}},
    }


def _build_flux2_klein_edit_workflow(
    prompt_text: str,
    input_image_name: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
    denoise: float,
    sampler_name: str,
    seed_value: int,
    filename_prefix: str,
) -> Dict[str, Any]:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_image_name}},
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX2_UNET}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX2_TEXT_ENCODER, "type": "flux2", "device": "default"}},
        "20": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "2": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["20", 0]}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": prompt_text}},
        "13": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["12", 0], "guidance": float(guidance)}},
        "18": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": int(width), "height": int(height), "batch_size": 1}},
        "43": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["13", 0], "latent": ["2", 0]}},
        "14": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["43", 0]}},
        "15": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler_name}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed_value, "mode": "fixed"}},
        "17": {"class_type": "Flux2Scheduler", "inputs": {"steps": int(steps), "width": int(width), "height": int(height)}},
        "44": {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["17", 0], "denoise": float(denoise)}},
        "19": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["14", 0], "sampler": ["15", 0], "sigmas": ["44", 1], "latent_image": ["18", 0]}},
        "21": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["20", 0]}},
        "22": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["21", 0]}},
    }


def _build_flux2_klein_inpaint_workflow(
    prompt_text: str,
    input_image_name: str,
    mask_image_name: str,
    mask_channel: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
    denoise: float,
    sampler_name: str,
    seed_value: int,
    filename_prefix: str,
    grow_mask_by: int,
    mask_expand: int,
) -> Dict[str, Any]:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_image_name}},
        "2": {"class_type": "LoadImageMask", "inputs": {"image": mask_image_name, "channel": mask_channel}},
        "3": {"class_type": "GrowMask", "inputs": {"mask": ["2", 0], "expand": int(mask_expand), "tapered_corners": True}},
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX2_UNET}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX2_TEXT_ENCODER, "type": "flux2", "device": "default"}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": prompt_text}},
        "13": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["12", 0], "guidance": float(guidance)}},
        "14": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["13", 0]}},
        "15": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler_name}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed_value, "mode": "fixed"}},
        "17": {"class_type": "Flux2Scheduler", "inputs": {"steps": int(steps), "width": int(width), "height": int(height)}},
        "18": {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["17", 0], "denoise": float(denoise)}},
        "20": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "21": {"class_type": "VAEEncodeForInpaint", "inputs": {"pixels": ["1", 0], "vae": ["20", 0], "mask": ["3", 0], "grow_mask_by": int(grow_mask_by)}},
        "22": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["21", 0], "mask": ["3", 0]}},
        "23": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["14", 0], "sampler": ["15", 0], "sigmas": ["18", 1], "latent_image": ["22", 0]}},
        "24": {"class_type": "VAEDecode", "inputs": {"samples": ["23", 0], "vae": ["20", 0]}},
        "25": {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["1", 0], "source": ["24", 0], "x": 0, "y": 0, "resize_source": False, "mask": ["3", 0]}},
        "26": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["25", 0]}},
    }


def _build_flux2_klein_outpaint_workflow(
    prompt_text: str,
    input_image_name: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
    denoise: float,
    sampler_name: str,
    seed_value: int,
    filename_prefix: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
    feathering: int,
    grow_mask_by: int,
) -> Dict[str, Any]:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_image_name}},
        "2": {"class_type": "ImagePadForOutpaint", "inputs": {"image": ["1", 0], "left": int(left), "top": int(top), "right": int(right), "bottom": int(bottom), "feathering": int(feathering)}},
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX2_UNET}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX2_TEXT_ENCODER, "type": "flux2", "device": "default"}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": prompt_text}},
        "13": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["12", 0], "guidance": float(guidance)}},
        "14": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["13", 0]}},
        "15": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler_name}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed_value, "mode": "fixed"}},
        "17": {"class_type": "Flux2Scheduler", "inputs": {"steps": int(steps), "width": int(width), "height": int(height)}},
        "18": {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["17", 0], "denoise": float(denoise)}},
        "20": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "21": {"class_type": "VAEEncodeForInpaint", "inputs": {"pixels": ["2", 0], "vae": ["20", 0], "mask": ["2", 1], "grow_mask_by": int(grow_mask_by)}},
        "22": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["21", 0], "mask": ["2", 1]}},
        "23": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["14", 0], "sampler": ["15", 0], "sigmas": ["18", 1], "latent_image": ["22", 0]}},
        "24": {"class_type": "VAEDecode", "inputs": {"samples": ["23", 0], "vae": ["20", 0]}},
        "25": {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["2", 0], "source": ["24", 0], "x": 0, "y": 0, "resize_source": False, "mask": ["2", 1]}},
        "26": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["25", 0]}},
    }


def _build_upscale_workflow(
    input_image_name: str,
    model_name: str,
    filename_prefix: str,
) -> Dict[str, Any]:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": input_image_name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": model_name}},
        "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["3", 0]}},
    }


def _save_result_image(img_info: Dict[str, Any], output_dir: str, output_filename: str, output_format: str) -> str:
    image_data = get_image_bytes(img_info["filename"], img_info.get("subfolder", ""), img_info.get("type", "output"))
    fmt = (output_format or "png").strip().lower()
    if fmt not in ("png", "webp"):
        raise ValueError('output_format must be "png" or "webp"')
    out_path = _safe_join_under_base(OUTPUT_BASE, output_dir, output_filename)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if fmt == "png":
        with open(out_path, "wb") as f:
            f.write(image_data)
    else:
        _maybe_convert_to_webp(image_data, out_path, DEFAULT_WEBP_QUALITY)
    return out_path


def _auto_output_filename(filename_prefix: str, prompt_id: str, output_format: str) -> str:
    ts = int(time.time())
    safe_prefix = "".join(c for c in (filename_prefix or "gen") if c.isalnum() or c in ("-", "_"))[:40] or "gen"
    ext = "png" if (output_format or "png").strip().lower() == "png" else "webp"
    return f"{safe_prefix}_{prompt_id}_{ts}.{ext}"


def _standard_result(prompt_id: str, seed_value: int, width: int, height: int, gen_w: int, gen_h: int, steps: int, guidance: float, sampler_name: str, scheduler: str, denoise: float, batch_size: int, output_path: str, extra: Optional[Dict[str, Any]] = None) -> str:
    result = {
        "status": "ok",
        "prompt_id": prompt_id,
        "seed": seed_value,
        "model": FLUX2_UNET,
        "text_encoder": FLUX2_TEXT_ENCODER,
        "vae": FLUX2_VAE,
        "requested_size": {"width": int(width), "height": int(height)},
        "generated_size": {"width": int(gen_w), "height": int(gen_h)},
        "steps": steps,
        "guidance": guidance,
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "denoise": denoise,
        "batch_size": batch_size,
        "output_path": output_path,
        "note": "After finishing your generation session, call unload_models() to free VRAM/RAM via ComfyUI /free.",
    }
    if extra:
        result.update(extra)
    return json.dumps(result, ensure_ascii=True)


@mcp.tool()
def generate_image(
    prompt_text: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    preset: str = "balanced",
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = DEFAULT_DENOISE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = DEFAULT_FILENAME_PREFIX,
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text must be a non-empty string")
    steps, guidance, preset_name = _resolve_preset(preset, steps, cfg)
    batch_size = int(batch_size)
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")

    prompt = _compose_prompt(prompt_text, negative_prompt)
    seed_value = secrets.randbits(63) if randomize_seed or seed is None else int(seed)
    gen_w, gen_h = _prepare_size(int(width), int(height))
    workflow = _build_flux2_klein_t2i_workflow(prompt, gen_w, gen_h, steps, guidance, sampler_name, seed_value, batch_size, filename_prefix)

    try:
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return _standard_result(prompt_id, seed_value, int(width), int(height), gen_w, gen_h, steps, guidance, sampler_name, scheduler, denoise, batch_size, out_path, {"preset": preset_name})
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def generate_image_i2i(
    input_image_path: str,
    prompt_text: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    width: int = 0,
    height: int = 0,
    preset: str = "balanced",
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = DEFAULT_DENOISE,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = "Flux2Klein9B_I2I",
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    """
    Image-to-image generation using FLUX.2 klein 9B Q5 GGUF.

    Notes:
      - Uploads the local input image to ComfyUI input storage automatically.
      - If width/height are omitted or set to 0, the local input image size is used.
      - `denoise` is used as a real strength control via `SplitSigmasDenoise`; lower values preserve more of the input image, higher values allow stronger changes.
    """
    if not isinstance(input_image_path, str) or not input_image_path.strip():
        raise ValueError("input_image_path must be a non-empty string")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text must be a non-empty string")
    steps, guidance, preset_name = _resolve_preset(preset, steps, cfg)

    if int(width) <= 0 or int(height) <= 0:
        width, height = _infer_local_image_size(input_image_path)
    prompt = _compose_prompt(prompt_text, negative_prompt)
    seed_value = secrets.randbits(63) if randomize_seed or seed is None else int(seed)
    gen_w, gen_h = _prepare_size(int(width), int(height))

    try:
        upload = _upload_input_image(input_image_path)
        input_name = upload.get("name")
        if not input_name:
            raise RuntimeError(f"Upload did not return input filename: {upload}")
        workflow = _build_flux2_klein_i2i_workflow(prompt, input_name, gen_w, gen_h, steps, guidance, denoise, sampler_name, seed_value, filename_prefix)
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return _standard_result(prompt_id, seed_value, int(width), int(height), gen_w, gen_h, steps, guidance, sampler_name, scheduler, denoise, 1, out_path, {"input_image_path": str(pathlib.Path(input_image_path).expanduser().resolve()), "uploaded_input_name": input_name, "preset": preset_name})
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def generate_image_edit(
    input_image_path: str,
    edit_instruction: str = "",
    prompt_text: str = "",
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    width: int = 0,
    height: int = 0,
    preset: str = "balanced",
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = DEFAULT_DENOISE,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = "Flux2Klein9B_Edit",
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    """
    Prompt-guided image editing using the FLUX.2 klein 9B ReferenceLatent path.

    This uses a ReferenceLatent-based edit path with real denoise-strength control, preserving more of the input composition than the plain i2i path while still allowing stronger edits when `denoise` is increased.
    """
    effective_prompt = (edit_instruction or prompt_text or "").strip()
    if not effective_prompt:
        raise ValueError("edit_instruction or prompt_text must be a non-empty string")
    if not isinstance(input_image_path, str) or not input_image_path.strip():
        raise ValueError("input_image_path must be a non-empty string")

    steps, guidance, preset_name = _resolve_preset(preset, steps, cfg)

    if int(width) <= 0 or int(height) <= 0:
        width, height = _infer_local_image_size(input_image_path)
    prompt = _compose_prompt(effective_prompt, negative_prompt)
    seed_value = secrets.randbits(63) if randomize_seed or seed is None else int(seed)
    gen_w, gen_h = _prepare_size(int(width), int(height))

    try:
        upload = _upload_input_image(input_image_path)
        input_name = upload.get("name")
        if not input_name:
            raise RuntimeError(f"Upload did not return input filename: {upload}")
        workflow = _build_flux2_klein_edit_workflow(prompt, input_name, gen_w, gen_h, steps, guidance, denoise, sampler_name, seed_value, filename_prefix)
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return _standard_result(prompt_id, seed_value, int(width), int(height), gen_w, gen_h, steps, guidance, sampler_name, scheduler, denoise, 1, out_path, {"input_image_path": str(pathlib.Path(input_image_path).expanduser().resolve()), "uploaded_input_name": input_name, "edit_instruction": effective_prompt, "preset": preset_name})
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def generate_image_inpaint(
    input_image_path: str,
    mask_image_path: str,
    prompt_text: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    mask_channel: str = "red",
    width: int = 0,
    height: int = 0,
    preset: str = "balanced",
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = 0.55,
    grow_mask_by: int = 12,
    mask_expand: int = 8,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = "Flux2Klein9B_Inpaint",
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    if not isinstance(input_image_path, str) or not input_image_path.strip():
        raise ValueError("input_image_path must be a non-empty string")
    if not isinstance(mask_image_path, str) or not mask_image_path.strip():
        raise ValueError("mask_image_path must be a non-empty string")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text must be a non-empty string")
    if mask_channel not in {"red", "green", "blue", "alpha"}:
        raise ValueError('mask_channel must be one of: "red", "green", "blue", "alpha"')
    steps, guidance, preset_name = _resolve_preset(preset, steps, cfg)
    if int(width) <= 0 or int(height) <= 0:
        width, height = _infer_local_image_size(input_image_path)
    prompt = _compose_prompt(prompt_text, negative_prompt)
    seed_value = secrets.randbits(63) if randomize_seed or seed is None else int(seed)
    gen_w, gen_h = _prepare_size(int(width), int(height))

    try:
        image_upload = _upload_input_image(input_image_path)
        mask_upload = _upload_input_image(mask_image_path)
        image_name = image_upload.get("name")
        mask_name = mask_upload.get("name")
        if not image_name or not mask_name:
            raise RuntimeError(f"Upload did not return input filenames: image={image_upload}, mask={mask_upload}")
        workflow = _build_flux2_klein_inpaint_workflow(prompt, image_name, mask_name, mask_channel, gen_w, gen_h, steps, guidance, denoise, sampler_name, seed_value, filename_prefix, grow_mask_by, mask_expand)
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return _standard_result(prompt_id, seed_value, int(width), int(height), gen_w, gen_h, steps, guidance, sampler_name, scheduler, denoise, 1, out_path, {"input_image_path": str(pathlib.Path(input_image_path).expanduser().resolve()), "mask_image_path": str(pathlib.Path(mask_image_path).expanduser().resolve()), "uploaded_input_name": image_name, "uploaded_mask_name": mask_name, "mask_channel": mask_channel, "grow_mask_by": int(grow_mask_by), "mask_expand": int(mask_expand), "preset": preset_name})
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def generate_image_outpaint(
    input_image_path: str,
    prompt_text: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    left: int = 256,
    top: int = 0,
    right: int = 256,
    bottom: int = 0,
    feathering: int = 40,
    width: int = 0,
    height: int = 0,
    preset: str = "balanced",
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
    sampler_name: str = DEFAULT_SAMPLER,
    scheduler: str = DEFAULT_SCHEDULER,
    denoise: float = 0.6,
    grow_mask_by: int = 12,
    seed: Optional[int] = None,
    randomize_seed: bool = True,
    filename_prefix: str = "Flux2Klein9B_Outpaint",
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    if not isinstance(input_image_path, str) or not input_image_path.strip():
        raise ValueError("input_image_path must be a non-empty string")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text must be a non-empty string")
    steps, guidance, preset_name = _resolve_preset(preset, steps, cfg)
    if min(int(left), int(top), int(right), int(bottom)) < 0:
        raise ValueError("left/top/right/bottom must be >= 0")
    if int(left) + int(top) + int(right) + int(bottom) <= 0:
        raise ValueError("at least one of left/top/right/bottom must be > 0")
    if int(width) <= 0 or int(height) <= 0:
        base_w, base_h = _infer_local_image_size(input_image_path)
        width = base_w + int(left) + int(right)
        height = base_h + int(top) + int(bottom)
    prompt = _compose_prompt(prompt_text, negative_prompt)
    seed_value = secrets.randbits(63) if randomize_seed or seed is None else int(seed)
    gen_w, gen_h = _prepare_size(int(width), int(height))

    try:
        image_upload = _upload_input_image(input_image_path)
        image_name = image_upload.get("name")
        if not image_name:
            raise RuntimeError(f"Upload did not return input filename: {image_upload}")
        workflow = _build_flux2_klein_outpaint_workflow(prompt, image_name, gen_w, gen_h, steps, guidance, denoise, sampler_name, seed_value, filename_prefix, left, top, right, bottom, feathering, grow_mask_by)
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return _standard_result(prompt_id, seed_value, int(width), int(height), gen_w, gen_h, steps, guidance, sampler_name, scheduler, denoise, 1, out_path, {"input_image_path": str(pathlib.Path(input_image_path).expanduser().resolve()), "uploaded_input_name": image_name, "left": int(left), "top": int(top), "right": int(right), "bottom": int(bottom), "feathering": int(feathering), "grow_mask_by": int(grow_mask_by), "preset": preset_name})
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def generate_image_upscale(
    input_image_path: str,
    upscale_model: str = DEFAULT_UPSCALE_MODEL,
    filename_prefix: str = "Flux2Klein9B_Upscale",
    output_dir: str = ".",
    output_filename: str = "",
    output_format: str = "png",
    max_wait_seconds: int = MAX_WAIT_SECONDS,
) -> str:
    """
    Upscale an input image using a lightweight ESRGAN-style upscaler such as 4x-UltraSharp.

    Notes:
      - Uploads the local input image to ComfyUI input storage automatically.
      - This path does not use the Flux2 UNet; it is intended as a fast post-processing step.
    """
    if not isinstance(input_image_path, str) or not input_image_path.strip():
        raise ValueError("input_image_path must be a non-empty string")
    if not isinstance(upscale_model, str) or not upscale_model.strip():
        raise ValueError("upscale_model must be a non-empty string")

    try:
        upload = _upload_input_image(input_image_path)
        input_name = upload.get("name")
        if not input_name:
            raise RuntimeError(f"Upload did not return input filename: {upload}")
        workflow = _build_upscale_workflow(input_name, upscale_model, filename_prefix)
        prompt_id, _client_id = queue_prompt(workflow)
        img_info = wait_for_first_image(prompt_id, int(max_wait_seconds))
        final_name = output_filename or _auto_output_filename(filename_prefix, prompt_id, output_format)
        out_path = _save_result_image(img_info, output_dir, final_name, output_format)
        return json.dumps({
            "status": "ok",
            "prompt_id": prompt_id,
            "operation": "upscale",
            "upscale_model": upscale_model,
            "input_image_path": str(pathlib.Path(input_image_path).expanduser().resolve()),
            "uploaded_input_name": input_name,
            "output_path": out_path,
            "note": "This lightweight post-processing path uses UpscaleModelLoader + ImageUpscaleWithModel.",
        }, ensure_ascii=True)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        return json.dumps({"status": "error", "error": "http_error", "details": str(e), "base_url": COMFYUI_BASE_URL}, ensure_ascii=True)
    except TimeoutError as e:
        return json.dumps({"status": "error", "error": "timeout", "details": str(e), "max_wait_seconds": int(max_wait_seconds)}, ensure_ascii=True)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unexpected", "details": str(e)}, ensure_ascii=True)


@mcp.tool()
def unload_models(unload_models: bool = True, free_memory: bool = True) -> str:
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
