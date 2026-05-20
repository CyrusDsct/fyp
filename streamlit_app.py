import hashlib
import io
import time

import pandas as pd
import streamlit as st
from PIL import Image

from analysis_core import run_memory_openrouter_analysis
from ui.sections.criteria import build_criteria_items, render_details_panel
from ui.sections.evaluation import render_evaluation
from ui.sections.upload_data import render_data_section
from utils.data_utils import coerce_numeric_series


SESSION_DEFAULTS = {
    "analysis_result": None,
    "analysis_error": None,
    "analysis_duration_s": None,
    "map_bytes": None,
    "map_name": None,
    "map_sig": None,
    "data_bytes": None,
    "data_name": None,
    "data_sig": None,
    "target_user": "",
    "map_purpose": "",
    "openrouter_api_key": "",
    "csv_df": None,
    "selected_column": None,
    "is_numeric_column": None,
    "binning_similarity": None,
    "_binning_diagnostics_cache": None,
}


def init_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_public_css() -> None:
    st.markdown(
        """
        <style>
        :root{
          --text:#111827;
          --muted:#6b7280;
          --line:#dde2e8;
          --accent:#f59e0b;
        }
        .block-container{
          max-width:1180px;
          padding-top:1.2rem;
          padding-bottom:2rem;
        }
        .top-row{
          display:flex;
          align-items:flex-end;
          justify-content:space-between;
          gap:1rem;
          margin-bottom:1rem;
        }
        .app-title{
          font-size:2.1rem;
          font-weight:950;
          line-height:1;
          color:var(--text);
        }
        .app-subtitle{
          margin-top:0.35rem;
          color:var(--muted);
          font-size:0.95rem;
        }
        .privacy-strip{
          border:1px solid #bbf7d0;
          border-radius:8px;
          background:#ecfdf3;
          color:#166534;
          padding:0.7rem 0.85rem;
          font-size:0.9rem;
          font-weight:750;
          margin-bottom:1rem;
        }
        .section-label{
          font-size:0.75rem;
          font-weight:900;
          letter-spacing:0.08em;
          color:var(--muted);
          margin:0 0 0.5rem;
        }
        .input-panel{
          border:1px solid var(--line);
          border-radius:8px;
          background:#fff;
          padding:0.9rem;
        }
        .result-panel{
          border:1px solid var(--line);
          border-radius:8px;
          background:#fff;
          padding:0.9rem;
          min-height:520px;
        }
        .overview-card,.criterion-card{
          border:1px solid #dde2e8;
          border-radius:8px;
          background:#fbfcfd;
          padding:0.95rem 1rem;
          margin-bottom:0.7rem;
        }
        .overview-score-card{
          border:1px solid #f6d08b;
          border-radius:8px;
          background:#fff7e6;
          padding:0.85rem 1rem;
          margin-bottom:0.7rem;
        }
        .overview-score-copy,.overview-section-title,.criterion-title{
          font-weight:900;
          color:#111827;
        }
        .overview-score-value{ color:#c2410c; }
        .overview-copy,.criterion-body{
          color:#374151;
          line-height:1.52;
          font-size:0.95rem;
        }
        .overview-highlight{
          background:#fff0b8;
          color:#6b4f00;
          border-radius:6px;
          padding:0.05rem 0.24rem;
          font-weight:900;
        }
        .overview-score-note-wrap,.criterion-head,.criterion-head-left{
          display:flex;
          flex-wrap:wrap;
          align-items:center;
          gap:0.45rem;
        }
        .criterion-head{ justify-content:space-between; margin-bottom:0.7rem; }
        .overview-score-pill,.criterion-chip,.criterion-topic-chip{
          display:inline-flex;
          align-items:center;
          border-radius:999px;
          padding:0.18rem 0.55rem;
          background:#eef2f7;
          color:#475569;
          font-size:0.74rem;
          font-weight:900;
        }
        .overview-score-pill.good,.criterion-chip.good{ background:#dcfce7; color:#166534; }
        .overview-score-pill.bad,.criterion-chip.bad{ background:#fee2e2; color:#991b1b; }
        .criterion-chip.meta{ background:#e0f2fe; color:#075985; }
        .criterion-row{ margin-bottom:0.65rem; }
        .criterion-key{
          color:#6b7280;
          font-size:0.72rem;
          font-weight:900;
          letter-spacing:0.05em;
          text-transform:uppercase;
          margin-bottom:0.18rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_analysis() -> None:
    st.session_state["analysis_result"] = None
    st.session_state["analysis_error"] = None
    st.session_state["analysis_duration_s"] = None
    st.session_state["binning_similarity"] = None
    st.session_state["_binning_diagnostics_cache"] = None


def store_uploaded_map(map_file) -> None:
    map_bytes = map_file.getvalue()
    map_sig = (map_file.name, len(map_bytes), hashlib.sha256(map_bytes).hexdigest())
    if st.session_state.get("map_sig") != map_sig:
        st.session_state["map_sig"] = map_sig
        reset_analysis()
    st.session_state["map_bytes"] = map_bytes
    st.session_state["map_name"] = map_file.name


def render_map_section() -> None:
    st.markdown('<div class="section-label">MAP</div>', unsafe_allow_html=True)
    map_file = st.file_uploader(
        "Upload map image",
        type=["png", "jpg", "jpeg"],
        key="public_map_uploader",
        label_visibility="collapsed",
    )
    if map_file is not None:
        store_uploaded_map(map_file)

    map_bytes = st.session_state.get("map_bytes")
    if not map_bytes:
        st.info("Upload a PNG or JPG map image.")
        return

    try:
        image = Image.open(io.BytesIO(map_bytes)).convert("RGB")
        st.image(image, caption=st.session_state.get("map_name", "Uploaded map"), width=360)
    except Exception:
        st.warning("Cannot preview this image.")


def selected_data_distribution_summary() -> str:
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
    median = float(values.quantile(0.5))
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


def render_key_section() -> None:
    st.markdown('<div class="section-label">OPENROUTER</div>', unsafe_allow_html=True)
    st.text_input(
        "OpenRouter API key",
        key="openrouter_api_key",
        type="password",
        placeholder="sk-or-v1-...",
    )
    st.caption("Used only for this analysis request. The app does not store it.")
    st.link_button("Get an OpenRouter key", "https://openrouter.ai/settings/keys", width="stretch")


def render_context_section() -> None:
    st.markdown('<div class="section-label">CONTEXT</div>', unsafe_allow_html=True)
    st.text_input("Target audience", key="target_user", placeholder="e.g. General public, Urban planners")
    st.text_input("Map purpose", key="map_purpose", placeholder="e.g. Show population density")


def run_analysis() -> None:
    key = str(st.session_state.get("openrouter_api_key") or "").strip()
    map_bytes = st.session_state.get("map_bytes")
    if not key:
        st.session_state["analysis_error"] = "OpenRouter API key is required."
        return
    if not map_bytes:
        st.session_state["analysis_error"] = "Map image is required."
        return

    progress = st.progress(0, text="Preparing image")
    started = time.time()
    try:
        progress.progress(15, text="Preparing image for model")
        distribution = selected_data_distribution_summary()
        progress.progress(35, text="Preparing data context")
        result = run_memory_openrouter_analysis(
            image_bytes=map_bytes,
            image_name=st.session_state.get("map_name", "map.png"),
            audience=st.session_state.get("target_user") or "unknown",
            purpose=st.session_state.get("map_purpose") or "unknown",
            distribution=distribution,
            api_key=key,
        )
        progress.progress(92, text="Rendering analysis")
        st.session_state["analysis_result"] = result
        st.session_state["analysis_error"] = None
        st.session_state["analysis_duration_s"] = round(time.time() - started, 2)
        progress.progress(100, text="Complete")
        time.sleep(0.3)
    except Exception as exc:
        st.session_state["analysis_error"] = str(exc)
        st.session_state["analysis_result"] = None
    finally:
        progress.empty()


def render_results() -> None:
    st.markdown('<div class="result-panel">', unsafe_allow_html=True)
    result = st.session_state.get("analysis_result")
    error = st.session_state.get("analysis_error")

    if error:
        st.error(error)
    elif not isinstance(result, dict):
        st.info("Upload a map, enter your own OpenRouter key, and run analysis.")
    else:
        analysis_json = result.get("analysis")
        if not isinstance(analysis_json, dict):
            st.error("Analysis result is not valid JSON.")
        else:
            items, _item_by_id = build_criteria_items(analysis_json)
            overview_tab, details_tab, raw_tab = st.tabs(["Overview", "Details", "JSON"])
            with overview_tab:
                duration = st.session_state.get("analysis_duration_s")
                if duration:
                    st.caption(f"Model: {result.get('model_used', 'unknown')} | Duration: {duration}s")
                render_evaluation(analysis_json, items)
            with details_tab:
                render_details_panel(analysis_json, items)
            with raw_tab:
                st.json(analysis_json)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Fixopleth", layout="wide")
    init_state()
    inject_public_css()

    st.markdown(
        """
        <div class="top-row">
          <div>
            <div class="app-title">Fixopleth</div>
            <div class="app-subtitle">Public choropleth map review using your own OpenRouter key.</div>
          </div>
        </div>
        <div class="privacy-strip">
          Privacy mode: no shared app key, no MongoDB writes, no upload folder, no public file URLs.
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_col, result_col = st.columns([0.95, 1.55], gap="large")
    with input_col:
        st.markdown('<div class="input-panel">', unsafe_allow_html=True)
        render_key_section()
        st.divider()
        render_map_section()
        st.divider()
        with st.expander("Data CSV", expanded=False):
            render_data_section()
        st.divider()
        render_context_section()
        st.divider()
        can_analyze = bool(st.session_state.get("map_bytes")) and bool(str(st.session_state.get("openrouter_api_key") or "").strip())
        if st.button("Analyze map", type="primary", disabled=not can_analyze, width="stretch"):
            run_analysis()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with result_col:
        render_results()


if __name__ == "__main__":
    main()
