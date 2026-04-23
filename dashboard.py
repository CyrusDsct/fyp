import time

import streamlit as st

from ui.components.scripts import inject_panel_height_js
from ui.components.styles import inject_base_css, inject_global_padding
from ui.sections.criteria import build_criteria_items, render_details_panel
from ui.sections.diagram import render_binning_details
from ui.sections.evaluation import render_evaluation
from ui.sections.start_analysis_sync import start_analysis_sync, sync_analysis_state
from ui.sections.upload_data import render_data_section
from ui.sections.upload_map import render_upload_map
from utils.json_utils import try_parse_json_text

BACKEND_BASE = "http://127.0.0.1:5000"
LEFT_PANEL_HEIGHT = 500
RIGHT_PANEL_HEIGHT = 525
SESSION_DEFAULTS = {
    "analysis_status": "idle",  # idle | running | done | error
    "analysis_result": None,
    "analysis_error": None,
    "analysis_started_at": None,
    "analysis_duration_s": None,
    "analysis_future": None,
    "analysis_request_id": None,
    "backend_image_id": None,
    "map_bytes": None,
    "map_name": None,
    "map_sig": None,
    "data_bytes": None,
    "data_name": None,
    "data_sig": None,
    "target_user": "",
    "map_purpose": "",
    "csv_df": None,
    "selected_column": None,
    "is_numeric_column": None,
    "binning_similarity": None,
    "left_tab": "Map",
    "right_tab": "Evaluation",
}
TITLE_HTML = """
<div class="top-title-wrap">
  <div class="top-title">Fixopleth</div>
</div>
"""
IDLE_PLACEHOLDER_HTML = (
    '<div class="right-placeholder">'
    '<div class="placeholder-guide">'
    '<div class="placeholder-title">How To Start</div>'
    '<div class="placeholder-step"><span class="step-label">Step 1</span> Upload a map in the <b>Map</b> tab.</div>'
    '<div class="placeholder-step"><span class="step-label">Step 2</span> Optionally add <b>Data</b> and <b>Context</b>.</div>'
    '<div class="placeholder-step"><span class="step-label">Step 3</span> Click <span class="placeholder-action">Analyze</span> to see the results!</div>'
    "</div>"
    "</div>"
)
RUNNING_STATE_HTML = (
    '<div class="running-state">'
    '<div class="running-badge">Running</div>'
    '<div class="running-title">Analyzing your map...</div>'
    '<div class="running-steps">'
    '<div class="running-step">1. Reading map content</div>'
    '<div class="running-step">2. Extracting legend and binning information</div>'
    '<div class="running-step">3. Building the right-side results view</div>'
    "</div>"
    "</div>"
)

st.set_page_config(
    page_title="Fixopleth",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)


def init_state():
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def unwrap_analysis_json(data):
    if not isinstance(data, dict):
        return data

    wrapped = data.get("choropleth_map_evaluation")
    if isinstance(wrapped, dict):
        return wrapped

    return data


def try_parse_result_and_show(result: dict):
    if isinstance(result, dict) and "analysis" in result:
        analysis_value = result.get("analysis", "")
        if isinstance(analysis_value, dict):
            st.json(analysis_value)
            return

        parsed = try_parse_json_text(analysis_value)
        if parsed is not None:
            st.json(parsed)
        else:
            st.text_area("Raw analysis (not valid JSON)", str(analysis_value), height=350)
            st.caption("Note: `analysis` is not valid JSON.")
    else:
        st.json(result)


def render_left_panel(content_renderer) -> None:
    with st.container(height=LEFT_PANEL_HEIGHT, border=False):
        st.markdown('<span class="panel-marker left-panel-marker"></span>', unsafe_allow_html=True)
        st.markdown('<div class="left-inner-pad">', unsafe_allow_html=True)
        content_renderer()
        st.markdown("</div>", unsafe_allow_html=True)


def render_context_section() -> None:
    st.markdown('<div class="section-label">CONTEXT</div>', unsafe_allow_html=True)
    st.text_input(
        "Target User",
        key="target_user",
        placeholder="e.g. General public, Urban planners",
    )
    st.text_input(
        "Map Purpose",
        key="map_purpose",
        placeholder="e.g. Show population density",
    )


def get_analysis_json(status: str, result: dict | None):
    if status != "done" or not isinstance(result, dict) or "analysis" not in result:
        return None

    analysis_raw = result.get("analysis")
    if isinstance(analysis_raw, dict):
        return unwrap_analysis_json(analysis_raw)

    parsed = try_parse_json_text(analysis_raw or "")
    if isinstance(parsed, dict):
        return unwrap_analysis_json(parsed)

    return None


def render_right_result_panel(analysis_json: dict, items: list[dict]) -> None:
    overview_tab, details_tab = st.tabs(["Overview", "Details"])

    with overview_tab:
        with st.container(height=RIGHT_PANEL_HEIGHT, border=False):
            st.markdown('<span class="panel-marker right-panel-marker"></span>', unsafe_allow_html=True)
            render_evaluation(analysis_json, items)

    with details_tab:
        with st.container(height=RIGHT_PANEL_HEIGHT, border=False):
            st.markdown('<span class="panel-marker right-panel-marker"></span>', unsafe_allow_html=True)
            detail_tabs = render_details_panel(analysis_json, items=items)
            if detail_tabs is not None:
                binning_tab, _ = detail_tabs
                with binning_tab:
                    render_binning_details(analysis_json)


def render_right_fallback_panel(status: str, result: dict | None, err: str | None) -> None:
    with st.container(height=RIGHT_PANEL_HEIGHT, border=False):
        st.markdown('<span class="panel-marker right-panel-marker"></span>', unsafe_allow_html=True)

        if status == "idle":
            st.markdown(IDLE_PLACEHOLDER_HTML, unsafe_allow_html=True)
        elif status == "running":
            st.markdown(RUNNING_STATE_HTML, unsafe_allow_html=True)
        elif status == "error":
            st.error(f"Analysis failed: {err or 'unknown error'}")
            st.caption(f"Make sure Flask backend is running at {BACKEND_BASE}")
        elif status == "done":
            st.caption("AI output is not valid JSON. Showing raw response.")
            if result is not None:
                try_parse_result_and_show(result)
        else:
            st.warning(f"Unknown analysis_status: {status}")


init_state()
sync_analysis_state()
inject_global_padding(padding_top_rem=0.0, padding_bottom_rem=0.0)
inject_base_css()
inject_panel_height_js()
st.markdown(TITLE_HTML, unsafe_allow_html=True)

left_col, right_col = st.columns([4, 6], gap="medium")

with left_col:
    st.markdown('<span class="col-marker left-col-marker"></span>', unsafe_allow_html=True)
    running = st.session_state.get("analysis_status") == "running"

    map_tab, data_tab, context_tab = st.tabs(["Map", "Data", "Context"])

    with map_tab:
        render_left_panel(lambda: render_upload_map(preview_box=280))

    with data_tab:
        render_left_panel(render_data_section)

    with context_tab:
        render_left_panel(render_context_section)

    has_map = bool(st.session_state.get("map_bytes"))
    btn_label = "Running..." if running else "Analyze"
    clicked = st.button(
        btn_label,
        disabled=(not has_map) or running,
        use_container_width=True,
        type="primary",
    )
    st.markdown('<div class="left-analyze-spacer"></div>', unsafe_allow_html=True)

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
    analysis_json = get_analysis_json(status, result)

    if analysis_json is not None:
        items, _ = build_criteria_items(analysis_json)
        render_right_result_panel(analysis_json, items)
    else:
        render_right_fallback_panel(status, result, err)

if st.session_state.get("analysis_status") == "running":
    time.sleep(1)
    st.rerun()
