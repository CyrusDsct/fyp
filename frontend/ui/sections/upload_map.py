import hashlib
import io

import streamlit as st
from PIL import Image

from front.ui.sections.start_analysis_sync import reset_analysis_state


def _store_uploaded_map(map_file) -> None:
    new_bytes = map_file.getvalue()
    new_name = map_file.name
    new_sig = (new_name, len(new_bytes), hashlib.sha256(new_bytes).hexdigest())
    prev_sig = st.session_state.get("map_sig")

    st.session_state["map_bytes"] = new_bytes
    st.session_state["map_name"] = new_name

    if prev_sig != new_sig:
        st.session_state["map_sig"] = new_sig
        st.session_state["backend_image_id"] = None
        reset_analysis_state()


def render_upload_map(preview_box: int = 280):
    st.markdown('<div class="section-label">UPLOAD MAP</div>', unsafe_allow_html=True)

    map_file = st.file_uploader(
        "Upload map image",
        type=["png", "jpg", "jpeg"],
        key="map_uploader",
        label_visibility="collapsed",
    )

    if map_file is not None:
        _store_uploaded_map(map_file)

    map_bytes = st.session_state.get("map_bytes")
    map_name = st.session_state.get("map_name", "Uploaded map")

    if not map_bytes:
        st.info("Please upload a map image.")
        return

    try:
        img = Image.open(io.BytesIO(map_bytes)).convert("RGB")
    except Exception:
        st.warning("Cannot read this image. Please upload a PNG/JPG.")
        return

    w, h = img.size
    scale = min(preview_box / w, preview_box / h)
    img_small = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    st.image(img_small, caption=map_name, width=preview_box)
