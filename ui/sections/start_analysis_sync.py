import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4

import streamlit as st

from backend_client import BackendClient

_ANALYSIS_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def get_backend() -> BackendClient:
    base_url = os.getenv("BACKEND_BASE", "http://127.0.0.1:5000")
    return BackendClient(base_url=base_url)


def reset_analysis_state(status: str = "idle") -> None:
    st.session_state["analysis_error"] = None
    st.session_state["analysis_result"] = None
    st.session_state["analysis_started_at"] = None
    st.session_state["analysis_duration_s"] = None
    st.session_state["analysis_request_id"] = None
    st.session_state["analysis_future"] = None
    st.session_state["analysis_status"] = status


def _set_analysis_duration() -> None:
    started_at = st.session_state.get("analysis_started_at")
    if started_at:
        st.session_state["analysis_duration_s"] = round(time.time() - started_at, 2)


def _run_analysis_job(
    request_id: str,
    map_bytes: bytes,
    map_name: str,
    existing_image_id: str | None,
    audience: str,
    purpose: str,
    distribution: str,
) -> dict:
    backend = get_backend()

    image_id = existing_image_id
    if not image_id:
        image_id = backend.upload_image(
            image_bytes=map_bytes,
            filename=map_name or "map.png",
        )

    result = backend.analyze(
        image_id=image_id,
        audience=audience,
        purpose=purpose,
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

    request_id = uuid4().hex

    reset_analysis_state(status="running")
    st.session_state["analysis_started_at"] = time.time()
    st.session_state["analysis_request_id"] = request_id

    future = _ANALYSIS_EXECUTOR.submit(
        _run_analysis_job,
        request_id,
        st.session_state["map_bytes"],
        st.session_state.get("map_name", "map.png"),
        st.session_state.get("backend_image_id"),
        st.session_state.get("target_user") or "unknown",
        st.session_state.get("map_purpose") or "unknown",
        "unknown",
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
            st.session_state["backend_image_id"] = payload.get("image_id")
            st.session_state["analysis_result"] = payload.get("result")
            _set_analysis_duration()
            st.session_state["analysis_status"] = "done"
    finally:
        if st.session_state.get("analysis_future") is future:
            st.session_state["analysis_future"] = None
