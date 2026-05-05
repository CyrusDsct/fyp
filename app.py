import os
import base64
import io
import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from bson.objectid import ObjectId
from openrouter import OpenRouter
from PIL import Image, UnidentifiedImageError
from pymongo import MongoClient
from werkzeug.utils import secure_filename

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

UPLOAD_FOLDER = "uploads/maps"
DATA_FOLDER = "uploads/data"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "csv"}
FILE_STORAGE = {
    "csv": {
        "config_key": "DATA_FOLDER",
        "url_prefix": "/uploads/data",
        "collection_name": "map_data",
    },
    "default": {
        "config_key": "UPLOAD_FOLDER",
        "url_prefix": "/uploads/maps",
        "collection_name": "map_images",
    },
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DATA_FOLDER"] = DATA_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

DEFAULT_OPENROUTER_MODELS = [
    "meta-llama/llama-4-maverick",
    "openai/gpt-5",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "qwen/qwen2.5-vl-72b-instruct",
]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def now_utc():
    return datetime.utcnow()


load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Missing MONGO_URI in environment (.env)")

client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)

db = client["MapAuditDB"]
results_collection = db["analysis_results"]
images_collection = db["map_images"]
data_collection = db["map_data"]
FILE_COLLECTIONS = (images_collection, data_collection)


PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")


def load_prompt_template() -> str:
    p = Path(PROMPT_PATH)
    if not p.exists():
        raise RuntimeError(f"prompt file not found: {p.resolve()}")
    return p.read_text(encoding="utf-8").strip()


def build_prompt(audience: str, purpose: str, distribution: str) -> str:
    template = load_prompt_template()
    return (
        template
        .replace("{{audience}}", str(audience or "unknown"))
        .replace("{{purpose}}", str(purpose or "unknown"))
        .replace("{{distribution}}", str(distribution or "unknown"))
    )


def read_image_path_from_db(image_id: str) -> tuple[str, str]:
    """Return (path, original_name) for stored map image."""
    img = images_collection.find_one({"_id": ObjectId(image_id)})
    if not img:
        raise FileNotFoundError("Image not found")

    image_path = img["url"].lstrip("/")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file missing: {image_path}")

    original_name = str(img.get("original_name") or os.path.basename(image_path))
    return image_path, original_name


def _parse_object_id(raw_id: str) -> ObjectId:
    try:
        return ObjectId(raw_id)
    except Exception as exc:
        raise ValueError("invalid image_id") from exc


def _get_storage_spec(filename: str) -> dict[str, str]:
    ext = filename.rsplit(".", 1)[1].lower()
    return FILE_STORAGE.get(ext, FILE_STORAGE["default"])


def _find_file_record(file_id: str) -> tuple[dict | None, Any | None]:
    oid = ObjectId(file_id)
    for collection in FILE_COLLECTIONS:
        record = collection.find_one({"_id": oid})
        if record:
            return record, collection
    return None, None


def _guess_mime_from_path(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".gif":
        return "image/gif"
    return "image/png"


def _get_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logging.warning("Invalid integer for %s=%r, using %r", name, raw, default)
        return default


def _get_env_int_list(name: str, default: list[int]) -> list[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default

    values = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            logging.warning("Skipping invalid integer in %s=%r", name, part)
            continue
        if value > 0:
            values.append(value)

    return values or default


def _split_env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _get_model_candidates() -> list[str]:
    primary = os.getenv("OPENROUTER_PRIMARY_MODEL", "").strip() or "meta-llama/llama-4-maverick"
    fallback_models = _split_env_list("OPENROUTER_FALLBACK_MODELS") or DEFAULT_OPENROUTER_MODELS[1:]

    models = [primary] + fallback_models
    deduped = []
    seen = set()
    for model in models:
        if model not in seen:
            seen.add(model)
            deduped.append(model)
    return deduped


def _unwrap_analysis_json(analysis_json: dict) -> dict:
    wrapped = analysis_json.get("choropleth_map_evaluation")
    if isinstance(wrapped, dict):
        return wrapped
    return analysis_json


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image

    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        merged = Image.alpha_composite(background, rgba)
        return merged.convert("RGB")

    return image.convert("RGB")


def _prepare_image_for_model(image_path: str, trace_id: str) -> tuple[str, str, dict]:
    fallback_mime = _guess_mime_from_path(image_path)
    max_dims = _get_env_int_list("OPENROUTER_IMAGE_MAX_DIMS", [1024, 768])
    jpeg_qualities = _get_env_int_list("OPENROUTER_IMAGE_QUALITIES", [85, 70])
    target_b64_len = _get_env_int("OPENROUTER_MAX_IMAGE_B64_LEN", 180000)
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

    try:
        with Image.open(image_path) as opened_image:
            original_size = opened_image.size
            source_image = opened_image.copy()
    except UnidentifiedImageError:
        with open(image_path, "rb") as file_obj:
            raw = file_obj.read()
        image_base64 = base64.b64encode(raw).decode("utf-8")
        meta = {
            "path": image_path,
            "original_size": None,
            "prepared_size": None,
            "bytes": len(raw),
            "b64_len": len(image_base64),
            "attempt": 0,
        }
        logging.info(
            "[%s] using original image bytes path=%s bytes=%d b64_len=%d",
            trace_id,
            image_path,
            len(raw),
            len(image_base64),
        )
        return fallback_mime, image_base64, meta

    last_payload = None
    attempt_count = max(len(max_dims), 1)
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
            "path": image_path,
            "original_size": {"width": original_size[0], "height": original_size[1]},
            "prepared_size": {"width": prepared.size[0], "height": prepared.size[1]},
            "bytes": len(raw),
            "b64_len": len(image_base64),
            "attempt": index,
            "quality": quality,
        }
        logging.info(
            "[%s] prepared image attempt %d/%d from %sx%s to %sx%s bytes=%d b64_len=%d",
            trace_id,
            index,
            attempt_count,
            original_size[0],
            original_size[1],
            prepared.size[0],
            prepared.size[1],
            len(raw),
            len(image_base64),
        )
        last_payload = ("image/jpeg", image_base64, meta)
        if len(image_base64) <= target_b64_len:
            break

    if last_payload is None:
        raise RuntimeError("Failed to prepare image payload for model")
    return last_payload

_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_FIRST_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip())


def _extract_first_json_object(text: str) -> str:
    """
    If model returns extra chatter (shouldn't, but happens),
    try to grab the first {...} block.
    """
    m = _FIRST_JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError("No JSON object found in model output")
    return m.group(0)


def parse_model_json(text: str) -> dict:
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        candidate = _extract_first_json_object(cleaned)
        return json.loads(candidate)


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        s = s.replace(",", "")
        try:
            return float(s)
        except Exception:
            return None
    return None


_RANGE_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

def normalize_range_value_to_intervals(range_value: Any) -> Optional[list[list[float]]]:
    """
    Accepts:
    - edges: [6,11,16,...]  -> intervals [[6,11],[11,16],...]
    - intervals: [[6,10.99],[11,15.99],...]
    - string: "6-10.99, 11-15.99, ..." or "6 – 10.99; 11 – 15.99"
    Returns: intervals or None
    """
    if range_value is None:
        return None

    if isinstance(range_value, list) and range_value and all(isinstance(it, list) for it in range_value):
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

    if isinstance(range_value, list) and range_value and all(not isinstance(it, list) for it in range_value):
        edges = [_to_float(v) for v in range_value]
        if any(v is None for v in edges):
            return None
        if len(edges) < 2:
            return None
        return [[edges[i], edges[i + 1]] for i in range(len(edges) - 1)]

    if isinstance(range_value, str):
        s = range_value.strip()
        nums = [float(n) for n in _RANGE_NUM_RE.findall(s)]
        if len(nums) >= 2 and len(nums) % 2 == 0:
            return [[nums[i], nums[i + 1]] for i in range(0, len(nums), 2)]
        if len(nums) >= 2:
            return [[nums[i], nums[i + 1]] for i in range(len(nums) - 1)]
        return None

    return None


def intervals_to_edges(intervals: list[list[float]]) -> Optional[list[float]]:
    if not intervals:
        return None
    edges = [intervals[0][0]]
    for lo, hi in intervals:
        edges.append(hi)
    return edges


def normalize_analysis(analysis_json: dict) -> dict:
    extract = analysis_json.get("extract")
    if not isinstance(extract, dict):
        return analysis_json

    range_obj = extract.get("RANGE")
    if not isinstance(range_obj, dict):
        return analysis_json

    rv = range_obj.get("value")
    intervals = normalize_range_value_to_intervals(rv)
    if intervals is not None:
        range_obj["intervals"] = intervals
        edges = intervals_to_edges(intervals)
        if edges is not None:
            range_obj["edges"] = edges
    else:
        range_obj.setdefault("intervals", "unknown")
        range_obj.setdefault("edges", "unknown")

    return analysis_json


def attach_input_context(analysis_json: dict, audience: str, purpose: str, distribution: str) -> dict:
    if not isinstance(analysis_json, dict):
        return analysis_json

    analysis_json["input_context"] = {
        "audience": str(audience or "unknown").strip() or "unknown",
        "purpose": str(purpose or "unknown").strip() or "unknown",
        "distribution": str(distribution or "unknown").strip() or "unknown",
    }
    return analysis_json


def _call_model(
    or_client: OpenRouter,
    model: str,
    prompt: str,
    mime: str,
    image_base64: str,
) -> str:
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

    response = or_client.chat.send(
        **kwargs
    )
    return response.choices[0].message.content


def _build_failure_result(
    *,
    trace_id: str,
    image_id: str,
    image_path: str,
    audience: str,
    purpose: str,
    distribution: str,
    model_candidates: list[str],
    image_meta: dict,
    last_error: Exception | None,
    analysis_raw: str | None,
    started_at: float,
) -> dict:
    error_message = str(last_error) if last_error else "All model attempts failed."
    results_collection.insert_one(
        {
            "trace_id": trace_id,
            "image_id": image_id,
            "analysis_raw": analysis_raw,
            "parse_error": error_message,
            "created_at": now_utc(),
            "audience": audience,
            "purpose": purpose,
            "distribution": distribution,
            "model_candidates": model_candidates,
            "image_meta": image_meta,
            "elapsed_s": round(time.time() - started_at, 3),
            "status": "model_failed",
        }
    )
    return {
        "status": "error",
        "error": error_message,
        "trace_id": trace_id,
        "image_path": image_path,
        "model_candidates": model_candidates,
    }


def _build_success_result(
    *,
    trace_id: str,
    image_id: str,
    image_path: str,
    original_name: str,
    audience: str,
    purpose: str,
    distribution: str,
    model_candidates: list[str],
    model_used: str,
    image_meta: dict,
    analysis_raw: str,
    analysis_json: dict,
    started_at: float,
) -> dict:
    results_collection.insert_one(
        {
            "trace_id": trace_id,
            "image_id": image_id,
            "analysis": analysis_json,
            "analysis_raw": analysis_raw,
            "created_at": now_utc(),
            "audience": audience,
            "purpose": purpose,
            "distribution": distribution,
            "model": model_used,
            "model_candidates": model_candidates,
            "image_path": image_path,
            "image_name": original_name,
            "image_meta": image_meta,
            "elapsed_s": round(time.time() - started_at, 3),
            "status": "ok",
        }
    )
    return {
        "status": "success",
        "trace_id": trace_id,
        "analysis": analysis_json,
        "analysis_raw": analysis_raw,
        "model_used": model_used,
        "model_candidates": model_candidates,
        "image_path": image_path,
        "image_name": original_name,
        "image_meta": image_meta,
    }


def _repair_to_json(or_client: OpenRouter, model: str, raw_text: str, trace_id: str) -> str:
    repair_prompt = (
        "You previously attempted to output JSON but it is not valid JSON.\n"
        "Fix it and output a SINGLE valid JSON object only. No markdown fences, no commentary.\n\n"
        "RAW OUTPUT:\n"
        f"{raw_text}"
    )
    logging.info("[%s] repairing invalid JSON via second pass...", trace_id)
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
    trace_id: str,
) -> tuple[str, dict]:
    analysis_raw = _call_model(or_client, model, prompt, mime, image_base64)

    try:
        analysis_json = parse_model_json(analysis_raw)
    except Exception as first_exc:
        logging.warning("[%s] invalid JSON on first pass for model=%s: %s", trace_id, model, str(first_exc))
        repaired_raw = _repair_to_json(or_client, model, analysis_raw, trace_id)
        try:
            analysis_json = parse_model_json(repaired_raw)
            analysis_raw = repaired_raw
        except Exception as second_exc:
            raise ValueError(
                f"Model returned invalid JSON (even after repair). first={first_exc}; second={second_exc}"
            ) from second_exc

    return analysis_raw, analysis_json


def run_openrouter_analysis(image_id: str, audience: str, purpose: str, distribution: str, trace_id: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY")

    model_candidates = _get_model_candidates()
    t0 = time.time()
    prompt = build_prompt(audience, purpose, distribution)
    image_path, original_name = read_image_path_from_db(image_id)
    mime, image_base64, image_meta = _prepare_image_for_model(image_path, trace_id)
    logging.info(
        "[%s] running analysis for file=%s original_name=%s models=%s prepared_b64_len=%d in %.2fs",
        trace_id,
        image_path,
        original_name,
        model_candidates,
        len(image_base64),
        time.time() - t0,
    )

    analysis_raw = None
    analysis_json = None
    model_used = None
    last_error = None
    with OpenRouter(api_key=api_key) as or_client:
        for model_name in model_candidates:
            try:
                logging.info("[%s] trying model=%s", trace_id, model_name)
                analysis_raw, analysis_json = _call_and_parse_model(
                    or_client,
                    model_name,
                    prompt,
                    mime,
                    image_base64,
                    trace_id,
                )
                model_used = model_name
                break
            except Exception as exc:
                last_error = exc
                logging.warning("[%s] model=%s failed, trying next fallback (%s)", trace_id, model_name, exc)

    if analysis_json is None or model_used is None or analysis_raw is None:
        return _build_failure_result(
            trace_id=trace_id,
            image_id=image_id,
            image_path=image_path,
            audience=audience,
            purpose=purpose,
            distribution=distribution,
            model_candidates=model_candidates,
            image_meta=image_meta,
            last_error=last_error,
            analysis_raw=analysis_raw,
            started_at=t0,
        )

    analysis_json = _unwrap_analysis_json(analysis_json)
    analysis_json = normalize_analysis(analysis_json)
    analysis_json = attach_input_context(analysis_json, audience, purpose, distribution)

    logging.info("[%s] model=%s returned and parsed in %.2fs", trace_id, model_used, time.time() - t0)

    return _build_success_result(
        trace_id=trace_id,
        image_id=image_id,
        image_path=image_path,
        original_name=original_name,
        audience=audience,
        purpose=purpose,
        distribution=distribution,
        model_candidates=model_candidates,
        model_used=model_used,
        image_meta=image_meta,
        analysis_raw=analysis_raw,
        analysis_json=analysis_json,
        started_at=t0,
    )


@app.route("/uploadImage", methods=["POST"])
def upload_image():
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        storage_spec = _get_storage_spec(filename)
        save_dir = app.config[storage_spec["config_key"]]
        url_path = f'{storage_spec["url_prefix"]}/{filename}'
        target_collection = db[storage_spec["collection_name"]]

        save_path = os.path.join(save_dir, filename)
        file.save(save_path)

        doc = {"original_name": file.filename, "url": url_path, "created_at": now_utc()}
        inserted_id = target_collection.insert_one(doc).inserted_id

        return jsonify({"status": "success", "image_id": str(inserted_id), "url": doc["url"]}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/readImage", methods=["GET"])
def read_images():
    try:
        images = []
        for collection in FILE_COLLECTIONS:
            images.extend(collection.find())
        for img in images:
            img["_id"] = str(img["_id"])
        return jsonify({"status": "success", "data": images}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/deleteImage/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    try:
        img_data, target_collection = _find_file_record(image_id)
        if not img_data:
            return jsonify({"status": "error", "message": "Image not found in database"}), 404

        file_path = img_data["url"].lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

        result = target_collection.delete_one({"_id": img_data["_id"]})
        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "database record deleted successfully"}), 200

        return jsonify({"status": "error", "message": "Delete failed"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/uploads/data/<filename>")
def serve_data(filename):
    return send_from_directory(app.config["DATA_FOLDER"], filename)


@app.route("/uploads/maps/<filename>")
def serve_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/analyze", methods=["POST"])
def analyze_sync():
    try:
        payload = request.get_json(silent=True) or {}
        image_id = payload.get("image_id")
        audience = payload.get("audience", "unknown")
        purpose = payload.get("purpose", "unknown")
        distribution = payload.get("distribution", "unknown")

        if not image_id:
            return jsonify({"status": "error", "error": "image_id is required"}), 400

        try:
            oid = _parse_object_id(image_id)
        except ValueError as exc:
            return jsonify({"status": "error", "error": str(exc)}), 400

        if not images_collection.find_one({"_id": oid}):
            return jsonify({"status": "error", "error": "image not found"}), 404

        trace_id = f"sync_{uuid.uuid4().hex}"
        result = run_openrouter_analysis(
            image_id=image_id,
            audience=audience,
            purpose=purpose,
            distribution=distribution,
            trace_id=trace_id,
        )
        code = 200 if result.get("status") == "success" else 502
        return jsonify(result), code

    except Exception as e:
        logging.exception("analyze failed")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": now_utc().isoformat()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000, use_reloader=False, threaded=True)
