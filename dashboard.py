# dashboard.py
import io
import time
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from ui.sections.diagram import render_classification_diagram
from ui.sections.evaluation import render_evaluation

from backend_client import BackendClient
from ui.sections.criteria import build_criteria_items, render_criteria
from ui.components.styles import inject_global_padding, inject_base_css
from ui.components.scripts import (
    inject_panel_height_js,
    inject_left_scroll_to_js,
    inject_right_scroll_to_js,
)
from utils.json_utils import try_parse_json_text
from ui.sections.upload_map import render_upload_map
from ui.sections.upload_data import render_data_section
from ui.sections.start_analysis_sync import start_analysis_sync

BACKEND_BASE = "http://127.0.0.1:5000"
backend = BackendClient(BACKEND_BASE)

st.set_page_config(page_title="Map Analysis", layout="wide")


def init_state():
    defaults = {
        # overall
        "analysis_status": "idle",  # idle | running | done | error
        "analysis_result": None,
        "analysis_error": None,
        "analysis_started_at": None,
        "analysis_duration_s": None,
        "backend_image_id": None,
        "map_bytes": None,
        "map_name": None,
        "map_sig": None,
        "data_bytes": None,
        "data_name": None,
        "enable_data_upload": False,
        "target_user": "",
        "map_purpose": "",
        "csv_df": None,
        "selected_column": None,
        "is_numeric_column": None,
        "binning_similarity": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

inject_global_padding(padding_top_rem=0.08, padding_bottom_rem=0.0)
inject_base_css()
inject_panel_height_js()


def try_parse_result_and_show(result: dict):
    if isinstance(result, dict) and "analysis" in result:
        analysis_text = result.get("analysis", "")
        parsed = try_parse_json_text(analysis_text)
        if parsed is not None:
            st.json(parsed)
        else:
            st.text_area("Raw analysis (not valid JSON)", str(analysis_text), height=350)
            st.caption("Note: 'analysis' is not valid JSON (or contains code fences).")
    else:
        st.json(result)


# =============================
# HEADER
# =============================
st.markdown(
    """
    <div class="top-title-wrap">
    <div class="top-title">How to NOT Lie With Map</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# MAIN PANELS
# =============================
left_col, right_col = st.columns([4, 6], gap="medium")

with left_col:
    st.markdown('<span class="col-marker left-col-marker"></span>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="left-sticky-headers" id="leftStickyHdr">
          <div class="hdr-row">
            <button type="button" data-target="sec-map">Map <span class="req-star">*</span></button>
            <button type="button" data-target="sec-data">Data</button>
            <button type="button" data-target="sec-context">Context</button>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=450, border=False):
        st.markdown('<span class="panel-marker left-panel-marker"></span>', unsafe_allow_html=True)
        st.markdown('<div class="left-inner-pad" id="leftInnerPad">', unsafe_allow_html=True)

        st.markdown('<div id="sec-map" class="section-anchor"></div>', unsafe_allow_html=True)
        render_upload_map(preview_box=280)

        st.markdown('<div id="sec-data" class="section-anchor"></div>', unsafe_allow_html=True)
        render_data_section()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div id="sec-context" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">CONTEXT</div>', unsafe_allow_html=True)
        st.text_input(
            "Who is this map for?",
            key="target_user",
            placeholder="e.g. General public, Urban planners…",
        )
        st.text_input(
            "What is the map for?",
            key="map_purpose",
            placeholder="e.g. Show population density…",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        inject_left_scroll_to_js()

        st.markdown("</div>", unsafe_allow_html=True)

    has_map = bool(st.session_state.get("map_bytes"))
    running = st.session_state.get("analysis_status") == "running"

    btn_label = "Running…" if running else "Analyze"
    clicked = st.button(btn_label, disabled=(not has_map) or running, use_container_width=True, type="primary")

    if clicked:
        try:
            start_analysis_sync()
        except Exception as e:
            st.session_state["analysis_error"] = str(e)
            st.session_state["analysis_status"] = "error"
        st.rerun()

with right_col:
    st.markdown('<span class="col-marker right-col-marker"></span>', unsafe_allow_html=True)

    status = st.session_state.get("analysis_status", "idle")
    result = st.session_state.get("analysis_result")
    err = st.session_state.get("analysis_error")

    analysis_json = None
    if status == "done" and isinstance(result, dict) and "analysis" in result:
        analysis_raw = result.get("analysis")

        if isinstance(analysis_raw, dict):
            analysis_json = analysis_raw
        else:
            parsed = try_parse_json_text(analysis_raw or "")
            if isinstance(parsed, dict):
                analysis_json = parsed
    show_right_header = analysis_json is not None

    if show_right_header:
        st.markdown(
            """
            <div class="right-fixed-headers" id="rightFixedHdr">
              <div class="hdr-row">
                <button type="button" data-target="r-sec-eval">AI Evaluation</button>
                <button type="button" data-target="r-sec-criteria">Criteria</button>
                <button type="button" data-target="r-sec-classify">Diagram</button>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(height=500, border=False):
        st.markdown('<span class="panel-marker right-panel-marker"></span>', unsafe_allow_html=True)

        if status == "idle":
            st.markdown(
                '<div class="right-placeholder">'
                'Upload a map and click <b> Analyze </b> to see results.'
                "</div>",
                unsafe_allow_html=True,
            )

        elif status == "running":
            st.info("Running… ")

        elif status == "error":
            st.error(f"Analysis failed: {err or 'unknown error'}")
            st.caption(f"Make sure Flask backend is running at {BACKEND_BASE}")

        elif status == "done":
            if result is None:
                st.warning("Analysis finished, but no results were produced.")
            else:
                backend_status = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
                if backend_status == "success":
                    st.success("Analysis complete.")
                else:
                    st.warning("Backend returned a non-success response.")

                dur = st.session_state.get("analysis_duration_s")
                if dur is not None:
                    st.caption(f"time: {dur}s")

            if analysis_json is None:
                st.caption("AI output is not valid JSON. Showing raw response.")
                if result is not None:
                    try_parse_result_and_show(result)
            else:
                items, item_by_label = build_criteria_items(analysis_json)

                st.markdown('<div id="r-sec-eval" class="right-section-anchor"></div>', unsafe_allow_html=True)
                render_evaluation(analysis_json, item_by_label)

                st.markdown('<div id="r-sec-criteria" class="right-section-anchor"></div>', unsafe_allow_html=True)
                render_criteria(analysis_json, items=items)

                st.markdown('<div id="r-sec-classify" class="right-section-anchor"></div>', unsafe_allow_html=True)
                render_classification_diagram(analysis_json)

        else:
            st.warning(f"Unknown analysis_status: {status}")

        if show_right_header:
            inject_right_scroll_to_js()