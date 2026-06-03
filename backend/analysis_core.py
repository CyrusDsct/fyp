from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from openrouter import OpenRouter
from PIL import Image, UnidentifiedImageError


DEFAULT_OPENROUTER_MODELS = [
    "meta-llama/llama-4-maverick",
    "openai/gpt-5",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "qwen/qwen2.5-vl-72b-instruct",
]

_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_FIRST_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)
_RANGE_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "docs" / "specifications" / "prompt.txt"


def _get_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_env_int_list(name: str, default: list[int]) -> list[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default

    values = []
    for part in raw.split(","):
        try:
            value = int(part.strip())
        except ValueError:
            continue
        if value > 0:
            values.append(value)
    return values or default


def _split_env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def get_model_candidates() -> list[str]:
    primary = os.getenv("OPENROUTER_PRIMARY_MODEL", "").strip() or DEFAULT_OPENROUTER_MODELS[0]
    fallback_models = _split_env_list("OPENROUTER_FALLBACK_MODELS") or DEFAULT_OPENROUTER_MODELS[1:]

    deduped = []
    seen = set()
    for model in [primary] + fallback_models:
        if model not in seen:
            seen.add(model)
            deduped.append(model)
    return deduped


def load_prompt_template() -> str:
    prompt_path = Path(os.getenv("PROMPT_PATH", str(DEFAULT_PROMPT_PATH)))
    if not prompt_path.is_absolute():
        prompt_path = PROJECT_ROOT / prompt_path
    if not prompt_path.exists():
        raise RuntimeError(f"prompt file not found: {prompt_path.resolve()}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_prompt(audience: str, purpose: str, distribution: str) -> str:
    template = load_prompt_template()
    return (
        template
        .replace("{{audience}}", str(audience or "unknown"))
        .replace("{{purpose}}", str(purpose or "unknown"))
        .replace("{{distribution}}", str(distribution or "unknown"))
    )


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image

    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        merged = Image.alpha_composite(background, rgba)
        return merged.convert("RGB")

    return image.convert("RGB")


def _guess_mime_from_filename(filename: str) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".gif":
        return "image/gif"
    return "image/png"


def prepare_image_bytes(image_bytes: bytes, filename: str, trace_id: str) -> tuple[str, str, dict]:
    fallback_mime = _guess_mime_from_filename(filename)
    max_dims = _get_env_int_list("OPENROUTER_IMAGE_MAX_DIMS", [1024, 768])
    jpeg_qualities = _get_env_int_list("OPENROUTER_IMAGE_QUALITIES", [85, 70])
    target_b64_len = _get_env_int("OPENROUTER_MAX_IMAGE_B64_LEN", 180000)
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

    try:
        with Image.open(io.BytesIO(image_bytes)) as opened_image:
            original_size = opened_image.size
            source_image = opened_image.copy()
    except UnidentifiedImageError:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        return fallback_mime, image_base64, {
            "original_size": None,
            "prepared_size": None,
            "bytes": len(image_bytes),
            "b64_len": len(image_base64),
            "attempt": 0,
        }

    last_payload = None
    for index, max_dim in enumerate(max_dims, start=1):
        quality = jpeg_qualities[min(index - 1, len(jpeg_qualities) - 1)]
        prepared = _flatten_to_rgb(source_image.copy())
        if max(prepared.size) > max_dim:
            prepared.thumbnail((max_dim, max_dim), resampling)

        buffer = io.BytesIO()
        prepared.save(buffer, format="JPEG", optimize=True, quality=quality)
        raw = buffer.getvalue()
        image_base64 = base64.b64encode(raw).decode("utf-8")
        meta = {
            "original_size": {"width": original_size[0], "height": original_size[1]},
            "prepared_size": {"width": prepared.size[0], "height": prepared.size[1]},
            "bytes": len(raw),
            "b64_len": len(image_base64),
            "attempt": index,
            "quality": quality,
            "trace_id": trace_id,
        }
        last_payload = ("image/jpeg", image_base64, meta)
        if len(image_base64) <= target_b64_len:
            break

    if last_payload is None:
        raise RuntimeError("Failed to prepare image payload for model")
    return last_payload


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip())


def _extract_first_json_object(text: str) -> str:
    match = _FIRST_JSON_OBJ_RE.search(text)
    if not match:
        raise ValueError("No JSON object found in model output")
    return match.group(0)


def parse_model_json(text: str) -> dict:
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        return json.loads(_extract_first_json_object(cleaned))


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().replace(",", ""))
        except ValueError:
            return None
    return None


def normalize_range_value_to_intervals(range_value: Any) -> Optional[list[list[float]]]:
    if range_value is None:
        return None

    if isinstance(range_value, list) and range_value and all(isinstance(item, list) for item in range_value):
        intervals = []
        for pair in range_value:
            if len(pair) != 2:
                return None
            lo = _to_float(pair[0])
            hi = _to_float(pair[1])
            if lo is None or hi is None:
                return None
            intervals.append([lo, hi])
        return intervals

    if isinstance(range_value, list) and range_value and all(not isinstance(item, list) for item in range_value):
        edges = [_to_float(value) for value in range_value]
        if any(value is None for value in edges) or len(edges) < 2:
            return None
        return [[edges[index], edges[index + 1]] for index in range(len(edges) - 1)]

    if isinstance(range_value, str):
        nums = [float(num) for num in _RANGE_NUM_RE.findall(range_value.strip())]
        if len(nums) >= 2 and len(nums) % 2 == 0:
            return [[nums[index], nums[index + 1]] for index in range(0, len(nums), 2)]
        if len(nums) >= 2:
            return [[nums[index], nums[index + 1]] for index in range(len(nums) - 1)]

    return None


def intervals_to_edges(intervals: list[list[float]]) -> Optional[list[float]]:
    if not intervals:
        return None
    edges = [intervals[0][0]]
    for _lo, hi in intervals:
        edges.append(hi)
    return edges


def normalize_analysis(analysis_json: dict) -> dict:
    extract = analysis_json.get("extract")
    if not isinstance(extract, dict):
        return analysis_json

    range_obj = extract.get("RANGE")
    if not isinstance(range_obj, dict):
        return analysis_json

    intervals = normalize_range_value_to_intervals(range_obj.get("value"))
    if intervals is not None:
        range_obj["intervals"] = intervals
        edges = intervals_to_edges(intervals)
        if edges is not None:
            range_obj["edges"] = edges
    else:
        range_obj.setdefault("intervals", "unknown")
        range_obj.setdefault("edges", "unknown")
    return analysis_json


def unwrap_analysis_json(analysis_json: dict) -> dict:
    wrapped = analysis_json.get("choropleth_map_evaluation")
    return wrapped if isinstance(wrapped, dict) else analysis_json


def attach_input_context(analysis_json: dict, audience: str, purpose: str, distribution: str) -> dict:
    analysis_json["input_context"] = {
        "audience": str(audience or "unknown").strip() or "unknown",
        "purpose": str(purpose or "unknown").strip() or "unknown",
        "distribution": str(distribution or "unknown").strip() or "unknown",
    }
    return analysis_json


def _call_model(or_client: OpenRouter, model: str, prompt: str, mime: str, image_base64: str) -> str:
    kwargs = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_base64}"}},
                ],
            }
        ],
    }
    max_tokens = _get_env_int("OPENROUTER_MAX_TOKENS")
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = or_client.chat.send(**kwargs)
    return response.choices[0].message.content


def _repair_to_json(or_client: OpenRouter, model: str, raw_text: str) -> str:
    repair_prompt = (
        "You previously attempted to output JSON but it is not valid JSON.\n"
        "Fix it and output a SINGLE valid JSON object only. No markdown fences, no commentary.\n\n"
        "RAW OUTPUT:\n"
        f"{raw_text}"
    )
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": repair_prompt}]}],
    }
    repair_max_tokens = _get_env_int("OPENROUTER_REPAIR_MAX_TOKENS")
    if repair_max_tokens is not None:
        kwargs["max_tokens"] = repair_max_tokens
    response = or_client.chat.send(**kwargs)
    return response.choices[0].message.content


def _call_and_parse_model(
    or_client: OpenRouter,
    model: str,
    prompt: str,
    mime: str,
    image_base64: str,
) -> tuple[str, dict]:
    analysis_raw = _call_model(or_client, model, prompt, mime, image_base64)
    try:
        return analysis_raw, parse_model_json(analysis_raw)
    except Exception as first_exc:
        repaired_raw = _repair_to_json(or_client, model, analysis_raw)
        try:
            return repaired_raw, parse_model_json(repaired_raw)
        except Exception as second_exc:
            raise ValueError(
                f"Model returned invalid JSON. first={first_exc}; second={second_exc}"
            ) from second_exc


def run_memory_openrouter_analysis(
    *,
    image_bytes: bytes,
    image_name: str,
    audience: str,
    purpose: str,
    distribution: str,
    api_key: str,
) -> dict:
    api_key = str(api_key or "").strip()
    if not api_key:
        raise RuntimeError("OpenRouter API key is required")
    if not image_bytes:
        raise RuntimeError("Map image is required")

    trace_id = f"public_{uuid.uuid4().hex}"
    started_at = time.time()
    prompt = build_prompt(audience, purpose, distribution)
    mime, image_base64, image_meta = prepare_image_bytes(image_bytes, image_name, trace_id)
    model_candidates = get_model_candidates()

    analysis_raw = None
    analysis_json = None
    model_used = None
    last_error = None

    with OpenRouter(api_key=api_key) as or_client:
        for model_name in model_candidates:
            try:
                analysis_raw, analysis_json = _call_and_parse_model(
                    or_client,
                    model_name,
                    prompt,
                    mime,
                    image_base64,
                )
                model_used = model_name
                break
            except Exception as exc:
                last_error = exc

    if analysis_json is None or model_used is None or analysis_raw is None:
        raise RuntimeError(str(last_error) if last_error else "All model attempts failed.")

    analysis_json = unwrap_analysis_json(analysis_json)
    analysis_json = normalize_analysis(analysis_json)
    analysis_json = attach_input_context(analysis_json, audience, purpose, distribution)

    return {
        "status": "success",
        "trace_id": trace_id,
        "analysis": analysis_json,
        "model_used": model_used,
        "model_candidates": model_candidates,
        "image_meta": image_meta,
        "elapsed_s": round(time.time() - started_at, 3),
    }
