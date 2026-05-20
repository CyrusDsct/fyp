import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4

import streamlit as st

from analysis_core import run_memory_openrouter_analysis
from backend_client import BackendClient
from utils.data_utils import coerce_numeric_series

_ANALYSIS_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def get_backend() -> BackendClient:
    base_url = os.getenv("BACKEND_BASE", "http://127.0.0.1:5000")
    return BackendClient(base_url=base_url)


def use_memory_analysis() -> bool:
    return os.getenv("FIXOPLETH_ANALYSIS_MODE", "").strip().lower() == "memory"


def reset_analysis_state(status: str = "idle") -> None:
    st.session_state["analysis_error"] = None
    st.session_state["analysis_result"] = None
    st.session_state["analysis_started_at"] = None
    st.session_state["analysis_duration_s"] = None
    st.session_state["analysis_request_id"] = None
    st.session_state["analysis_future"] = None
    st.session_state["analysis_status"] = status
    st.session_state["binning_similarity"] = None
    st.session_state["_binning_diagnostics_cache"] = None
    st.session_state["_completing_until"] = None


def _set_analysis_duration() -> None:
    started_at = st.session_state.get("analysis_started_at")
    if started_at:
        st.session_state["analysis_duration_s"] = round(time.time() - started_at, 2)


def _selected_data_distribution_summary() -> str:
    csv_df = st.session_state.get("csv_df")
    selected_column = st.session_state.get("selected_column")
    if csv_df is None or not selected_column or selected_column not in getattr(csv_df, "columns", []):
        return "unknown"

    try:
        values = coerce_numeric_series(csv_df[selected_column]).dropna()
    except Exception:
        return "unknown"

    if values.empty:
        return "unknown"

    count = int(values.shape[0])
    min_value = float(values.min())
    q1 = float(values.quantile(0.25))
    median = float(values.median())
    q3 = float(values.quantile(0.75))
    max_value = float(values.max())
    mean = float(values.mean())
    skewness = float(values.skew()) if count >= 3 else 0.0
    unique_count = int(values.nunique(dropna=True))

    if abs(skewness) >= 1:
        shape = "strongly skewed"
    elif abs(skewness) >= 0.5:
        shape = "moderately skewed"
    else:
        shape = "roughly symmetric"

    return (
        f"CSV column '{selected_column}' has {count} numeric values, {unique_count} unique values, "
        f"min={min_value:.4g}, Q1={q1:.4g}, median={median:.4g}, Q3={q3:.4g}, "
        f"max={max_value:.4g}, mean={mean:.4g}, skewness={skewness:.3g} ({shape})."
    )


def _run_analysis_job(
    request_id: str,
    map_bytes: bytes,
    map_name: str,
    audience: str,
    purpose: str,
    openrouter_api_key: str,
    distribution: str,
) -> dict:
    if use_memory_analysis():
        result = run_memory_openrouter_analysis(
            image_bytes=map_bytes,
            image_name=map_name or "map.png",
            audience=audience,
            purpose=purpose,
            distribution=distribution,
            api_key=openrouter_api_key,
        )
        return {
            "request_id": request_id,
            "image_id": None,
            "result": result,
        }

    backend = get_backend()

    image_id = backend.upload_image(
        image_bytes=map_bytes,
        filename=map_name or "map.png",
    )

    result = backend.analyze(
        image_id=image_id,
        audience=audience,
        purpose=purpose,
        openrouter_api_key=openrouter_api_key,
        distribution=distribution,
    )

    return {
        "request_id": request_id,
        "image_id": image_id,
        "result": result,
    }


def start_analysis_sync() -> None:
    if not st.session_state.get("map_bytes"):
        raise RuntimeError("No map uploaded.")

    openrouter_api_key = str(st.session_state.get("openrouter_api_key") or "").strip()
    if not openrouter_api_key:
        raise RuntimeError("OpenRouter API key is required.")

    request_id = uuid4().hex

    reset_analysis_state(status="running")
    st.session_state["analysis_started_at"] = time.time()
    st.session_state["analysis_request_id"] = request_id

    future = _ANALYSIS_EXECUTOR.submit(
        _run_analysis_job,
        request_id,
        st.session_state["map_bytes"],
        st.session_state.get("map_name", "map.png"),
        st.session_state.get("target_user") or "unknown",
        st.session_state.get("map_purpose") or "unknown",
        openrouter_api_key,
        _selected_data_distribution_summary(),
    )
    st.session_state["analysis_future"] = future


def sync_analysis_state() -> None:
    future = st.session_state.get("analysis_future")
    if not isinstance(future, Future):
        return

    if not future.done():
        return

    current_request_id = st.session_state.get("analysis_request_id")

    try:
        payload = future.result()
    except Exception as exc:
        if current_request_id:
            st.session_state["analysis_error"] = str(exc)
            st.session_state["analysis_status"] = "error"
            _set_analysis_duration()
    else:
        if payload.get("request_id") == current_request_id:
            st.session_state["backend_image_id"] = None
            st.session_state["analysis_result"] = payload.get("result")
            _set_analysis_duration()
            st.session_state["analysis_status"] = "done"
            st.session_state["_completing_until"] = time.time() + 1.0
    finally:
        if st.session_state.get("analysis_future") is future:
            st.session_state["analysis_future"] = None
