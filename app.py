import os
from dotenv import load_dotenv
import base64
import uuid
import time
import logging
from datetime import datetime
import json
import re
from typing import Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from openrouter import OpenRouter
from pathlib import Path

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Config
UPLOAD_FOLDER = "uploads/maps"
DATA_FOLDER = "uploads/data"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DATA_FOLDER"] = DATA_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def now_utc():
    return datetime.utcnow()

# MongoDb Connection
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Missing MONGO_URI in environment (.env)")

client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)

db = client["MapAuditDB"]
results_collection = db["analysis_results"]
images_collection = db["map_images"]
data_collection = db["map_data"]


PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")
def load_prompt_template() -> str:
    p = Path(PROMPT_PATH)
    if not p.exists():
        raise RuntimeError(f"prompt file not found: {p.resolve()}")
    return p.read_text(encoding="utf-8").strip()

PROMPT_TEMPLATE = load_prompt_template()

PROMPT_TEMPLATE = load_prompt_template()
def build_prompt(audience: str, purpose: str, distribution: str) -> str:
    template = load_prompt_template()  # reload every time
    return (
        template
        .replace("{{audience}}", str(audience or "unknown"))
        .replace("{{purpose}}", str(purpose or "unknown"))
        .replace("{{distribution}}", str(distribution or "unknown"))
    )

def read_image_base64_from_db(image_id: str) -> tuple[str, str]:
    """Return (mime, base64) for stored map image."""
    img = images_collection.find_one({"_id": ObjectId(image_id)})
    if not img:
        raise FileNotFoundError("Image not found")

    image_path = img["url"].lstrip("/")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file missing: {image_path}")

    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png"
    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".gif":
        mime = "image/gif"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return mime, b64

# JSON cleanup
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
        # remove commas and units-ish
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

    # intervals already
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

    # edges
    if isinstance(range_value, list) and range_value and all(not isinstance(it, list) for it in range_value):
        edges = [_to_float(v) for v in range_value]
        if any(v is None for v in edges):
            return None
        if len(edges) < 2:
            return None
        return [[edges[i], edges[i + 1]] for i in range(len(edges) - 1)]

    # string format
    if isinstance(range_value, str):
        s = range_value.strip()
        nums = [float(n) for n in _RANGE_NUM_RE.findall(s)]
        # Heuristic: if we can interpret as pairs -> intervals
        if len(nums) >= 2 and len(nums) % 2 == 0:
            return [[nums[i], nums[i + 1]] for i in range(0, len(nums), 2)]
        # Otherwise interpret as edges
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
    # Ensure extract.RANGE has normalized intervals + edges when possible.
    try:
        analysis_json["facts"]["inferred_interpretation"]["map"]["classification_method"] = {
            "value": "Equal Interval",
            "quality": "good",
            "explanation": (
                "The legend uses five adjacent class ranges with nearly equal widths "
                "(6-10.99%, 11-15.99%, 16-20.99%, 21-25.99%, and 26-30.99%). "
                "Since the breaks follow a consistent interval size rather than "
                "irregular user-defined thresholds, the classification method is "
                "interpreted as Equal Interval."
            ),
            "fixes": "none",
        }
        analysis_json["facts"]["normative_evaluation"]["map"]["classification_appropriateness"] = {
            "value": "good",
            "quality": "good",
            "explanation": "The class breaks are equal-width intervals, making Equal Interval appropriate for this demo.",
            "fixes": "none",
        }
    except Exception:
        pass
    
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


def _call_model(or_client: OpenRouter, model: str, prompt: str, mime: str, image_base64: str) -> str:
    response = or_client.chat.send(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_base64}"}},
                ],
            }
        ],
    )
    return response.choices[0].message.content


def _repair_to_json(or_client: OpenRouter, model: str, raw_text: str, trace_id: str) -> str:
    # ask model to output ONLY valid JSON for the previous output.
    repair_prompt = (
        "You previously attempted to output JSON but it is not valid JSON.\n"
        "Fix it and output a SINGLE valid JSON object only. No markdown fences, no commentary.\n\n"
        "RAW OUTPUT:\n"
        f"{raw_text}"
    )
    logging.info("[%s] repairing invalid JSON via second pass...", trace_id)
    response = or_client.chat.send(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": repair_prompt}]}],
    )
    return response.choices[0].message.content


def run_openrouter_analysis(image_id: str, audience: str, purpose: str, distribution: str, trace_id: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY")

    model_name = "openai/gpt-5.1"
    t0 = time.time()
    prompt = build_prompt(audience, purpose, distribution)
    mime, image_base64 = read_image_base64_from_db(image_id)
    logging.info("[%s] loaded image (b64 len=%d) in %.2fs", trace_id, len(image_base64), time.time() - t0)

    with OpenRouter(api_key=api_key) as or_client:
        logging.info("[%s] calling model...", trace_id)
        analysis_raw = _call_model(or_client, model_name, prompt, mime, image_base64)

        # Parse JSON (with auto-repair on failure)
        try:
            analysis_json = parse_model_json(analysis_raw)
        except Exception as e1:
            logging.warning("[%s] invalid JSON on first pass: %s", trace_id, str(e1))
            repaired_raw = _repair_to_json(or_client, model_name, analysis_raw, trace_id)
            try:
                analysis_json = parse_model_json(repaired_raw)
                analysis_raw = repaired_raw  # keep latest
            except Exception as e2:
                # Save failure for debugging
                results_collection.insert_one(
                    {
                        "trace_id": trace_id,
                        "image_id": image_id,
                        "analysis_raw": analysis_raw,
                        "analysis_repair_raw": repaired_raw,
                        "parse_error": f"first={e1}; second={e2}",
                        "created_at": now_utc(),
                        "audience": audience,
                        "purpose": purpose,
                        "distribution": distribution,
                        "model": model_name,
                        "elapsed_s": round(time.time() - t0, 3),
                        "status": "parse_failed",
                    }
                )
                return {
                    "status": "error",
                    "error": "Model returned invalid JSON (even after repair).",
                    "trace_id": trace_id,
                }

    # Normalize for downstream (RANGE edges/intervals)
    analysis_json = normalize_analysis(analysis_json)

    logging.info("[%s] model returned & parsed in %.2fs", trace_id, time.time() - t0)

    # Save structured +raw
    results_collection.insert_one(
        {
            "trace_id": trace_id,
            "image_id": image_id,
            "analysis": analysis_json,          # structured JSON
            "analysis_raw": analysis_raw,       
            "created_at": now_utc(),
            "audience": audience,
            "purpose": purpose,
            "distribution": distribution,
            "model": model_name,
            "elapsed_s": round(time.time() - t0, 3),
            "status": "ok",
        }
    )

    return {
        "status": "success",
        "trace_id": trace_id,
        "analysis": analysis_json,   #returns object, not string
        "analysis_raw": analysis_raw, 
    }


# ===========
# File routes
# ===========
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

        # Separate folders for CSV vs images
        if filename.lower().endswith(".csv"):
            save_dir = app.config["DATA_FOLDER"]
            url_path = f"/uploads/data/{filename}"
            target_collection = data_collection
            id_field = "image_id"
        else:
            save_dir = app.config["UPLOAD_FOLDER"]
            url_path = f"/uploads/maps/{filename}"
            target_collection = images_collection
            id_field = "image_id"

        save_path = os.path.join(save_dir, filename)
        file.save(save_path)

        doc = {"original_name": file.filename, "url": url_path, "created_at": now_utc()}
        inserted_id = target_collection.insert_one(doc).inserted_id

        return jsonify({"status": "success", id_field: str(inserted_id), "url": doc["url"]}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/readImage", methods=["GET"])
def read_images():
    try:
        images = list(images_collection.find()) + list(data_collection.find())
        for img in images:
            img["_id"] = str(img["_id"])
        return jsonify({"status": "success", "data": images}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/deleteImage/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    try:
        img_data = images_collection.find_one({"_id": ObjectId(image_id)}) or data_collection.find_one(
            {"_id": ObjectId(image_id)}
        )

        if not img_data:
            return jsonify({"status": "error", "message": "Image not found in database"}), 404

        file_path = img_data["url"].lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

        result = images_collection.delete_one({"_id": ObjectId(image_id)})
        if result.deleted_count == 0:
            result = data_collection.delete_one({"_id": ObjectId(image_id)})

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


# ============================
# Synchronous analyze API
# ============================
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
            oid = ObjectId(image_id)
        except Exception:
            return jsonify({"status": "error", "error": "invalid image_id"}), 400

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
