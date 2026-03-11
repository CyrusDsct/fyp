import os
import time
import streamlit as st
from backend_client import BackendClient

def get_backend() -> BackendClient:
    base_url = os.getenv("BACKEND_BASE", "http://127.0.0.1:5000")
    return BackendClient(base_url=base_url)

def start_analysis_sync():
    if not st.session_state.get("map_bytes"):
        raise RuntimeError("No map uploaded.")

    backend = get_backend()

    st.session_state["analysis_error"] = None
    st.session_state["analysis_result"] = None
    st.session_state["analysis_status"] = "running"
    st.session_state["analysis_started_at"] = time.time()
    st.session_state["analysis_duration_s"] = None

    image_id = st.session_state.get("backend_image_id")
    if not image_id:
        with st.spinner("Uploading map…"):
            image_id = backend.upload_image(
                image_bytes=st.session_state["map_bytes"],
                filename=st.session_state.get("map_name", "map.png"),
            )
        st.session_state["backend_image_id"] = image_id

    audience = st.session_state.get("target_user") or "unknown"
    purpose = st.session_state.get("map_purpose") or "unknown"
    distribution = "unknown"

    with st.spinner("Running analysis…"):
        result = backend.analyze(
            image_id=image_id,
            audience=audience,
            purpose=purpose,
            distribution=distribution,
        )

    st.session_state["analysis_result"] = result
    st.session_state["analysis_duration_s"] = round(
        time.time() - st.session_state["analysis_started_at"], 2
    )
    st.session_state["analysis_status"] = "done"