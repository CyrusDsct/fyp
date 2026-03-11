import io
import pandas as pd
import streamlit as st
from ui.sections.plot_disturbution import plot_distribution

def render_data_section():
    st.markdown("<hr>", unsafe_allow_html=True)
    st.checkbox("Upload Data (optional)", key="enable_data_upload")

    if not st.session_state.get("enable_data_upload"):
        st.session_state["csv_df"] = None
        st.session_state["selected_column"] = None
        st.session_state["is_numeric_column"] = None
        return

    st.markdown('<div class="section-label">UPLOAD DATA</div>', unsafe_allow_html=True)

    data_file = st.file_uploader(
        "Upload data (CSV)",
        type=["csv"],
        key="data_uploader",
        label_visibility="collapsed",
    )

    if data_file is not None:
        st.session_state["data_bytes"] = data_file.getvalue()
        st.session_state["data_name"] = data_file.name
        st.session_state.pop("data_attr", None)

    if not st.session_state.get("data_bytes"):
        st.caption("Upload a CSV to enable attribute selection.")
        return

    try:
        df = pd.read_csv(io.BytesIO(st.session_state["data_bytes"]))
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(st.session_state["data_bytes"]), encoding="utf-8-sig")
    except Exception as e:
        st.error(f"Cannot read CSV: {e}")
        return

    st.caption(
        f"**{st.session_state.get('data_name', '(uploaded)')}** · "
        f"rows: **{len(df)}** · cols: **{df.shape[1]}**"
    )
    if df.shape[1] == 0:
        st.warning("CSV has no columns.")
        return

    cols = list(df.columns)

    if "data_attr" not in st.session_state or st.session_state["data_attr"] not in cols:
        st.session_state["data_attr"] = cols[0]

    st.markdown('<div class="section-label">ATTRIBUTE</div>', unsafe_allow_html=True)
    sel_col, data_col = st.columns([2, 3], vertical_alignment="top")

    with sel_col:
        current_idx = cols.index(st.session_state["data_attr"])
        picked = st.radio(
            "Choose attribute",
            options=cols,
            index=current_idx,
            key="data_attr_radio_ui",
            label_visibility="collapsed",
        )
        st.session_state["data_attr"] = picked

    selected = st.session_state["data_attr"]

    st.session_state["csv_df"] = df
    st.session_state["selected_column"] = selected
    try:
        numeric_series = pd.to_numeric(df[selected], errors="coerce")
        st.session_state["is_numeric_column"] = (numeric_series.notna().sum() > 0)
    except Exception:
        st.session_state["is_numeric_column"] = False

    with data_col:
        st.dataframe(
            df[[selected]],
            height=220,
            use_container_width=True,
            key=f"data_preview__{selected}",
        )

    plot_distribution(df[selected])
