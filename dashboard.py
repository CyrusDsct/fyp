# dashboard.py
import json
from io import StringIO

import numpy as np
import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt

from binning import BIN_METHODS, interval_similarity
from analysis_helper import (
    parse_analysis_json,
    get_overall_text,
    evaluate_fields,
    status_to_icon,
    get_value_by_path,
)

API_BASE_URL = "http://127.0.0.1:5000"

# Web style
st.set_page_config(
    page_title="How to Not Lie With Maps",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1400px;
    }
    hr {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .centered-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
        margin-bottom: 0.8rem;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        system-ui, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="centered-title">How to Not Lie With Maps</h1>',
    unsafe_allow_html=True,
)


# Restart Button

top_left, top_middle, top_right = st.columns([4, 4, 1])
with top_right:
    if st.button("Restart", type="secondary"):
        st.session_state.clear()
        st.rerun()


default_session = {
    "analysis": None,
    "map_bytes": None,
    "map_name": None,
    "selected_column": None,
    "selected_criterion": None,
    "csv_df": None,
    "binning_similarity": None,  
}
for k, v in default_session.items():
    if k not in st.session_state:
        st.session_state[k] = v

#Top layout: Map + Data
top_left, top_right = st.columns([1, 1])

with top_left:
    st.markdown("### 🗺️ Map")
    map_file = st.file_uploader(
        "Upload map image",
        type=["png", "jpg", "jpeg"],
        key="map_uploader",
        label_visibility="collapsed",
    )
    if map_file is not None:
        st.session_state["map_bytes"] = map_file.getvalue()
        st.session_state["map_name"] = map_file.name

    map_container = st.container()
    with map_container:
        if st.session_state.get("map_bytes"):
            st.image(
                st.session_state["map_bytes"],
                caption=st.session_state.get("map_name", "Uploaded map"),
                use_container_width=True,
            )
        else:
            st.info("Please upload a map image.")

with top_right:
    st.markdown("### 📊 Data")
    csv_file = st.file_uploader(
        "Upload CSV data",
        type=["csv"],
        key="csv_uploader",
        label_visibility="collapsed",
    )

    selected_column = None
    csv_df = st.session_state.get("csv_df")

    if csv_file is not None:
        try:
            csv_bytes = csv_file.getvalue()
            csv_str = csv_bytes.decode("utf-8", errors="ignore")
            csv_df_local = pd.read_csv(StringIO(csv_str))
            st.session_state["csv_df"] = csv_df_local
            csv_df = csv_df_local

            st.write(f"File: **{csv_file.name}**")
            st.write(f"Rows: `{len(csv_df)}`, Columns: `{len(csv_df.columns)}`")

            upper, lower = st.columns([1, 1])

            with upper:
                st.subheader("Available columns")
                selected_column = st.radio(
                    "Choose a column to analyze (required)",
                    options=list(csv_df.columns),
                    index=None,
                    key="column_selector",
                )

            with lower:
                st.subheader("Column preview")
                if selected_column:
                    preview_df = csv_df[[selected_column]]
                    st.dataframe(
                        preview_df,
                        use_container_width=True,
                        height=240,
                    )
                else:
                    st.info("Select a column to preview its values.")

        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

    elif csv_df is not None:
        st.write(f"Rows: `{len(csv_df)}`, Columns: `{len(csv_df.columns)}`")
        upper, lower = st.columns([1, 1])
        with upper:
            st.subheader("Available columns")
            selected_column = st.radio(
                "Choose a column to analyze (required)",
                options=list(csv_df.columns),
                index=None,
                key="column_selector",
            )
        with lower:
            st.subheader("Column preview")
            if selected_column:
                st.dataframe(
                    csv_df[[selected_column]],
                    use_container_width=True,
                    height=240,
                )
            else:
                st.info("Select a column to preview its values.")

    if selected_column:
        st.session_state["selected_column"] = selected_column

st.markdown("<hr>", unsafe_allow_html=True)

# Center: START button
center_col = st.columns([3, 2, 3])[1]

has_map = st.session_state.get("map_bytes") is not None
has_csv = st.session_state.get("csv_df") is not None
has_col = st.session_state.get("selected_column") is not None
btn_enabled = has_map and has_csv and has_col

with center_col:
    if not btn_enabled:
        st.button(
            "START ANALYSIS",
            use_container_width=True,
            type="secondary",
            disabled=True,
        )
        st.caption("Upload map + CSV and choose a column to enable the overall analysis.")
    else:
        start_clicked = st.button(
            "🚀 START ANALYSIS",
            use_container_width=True,
            type="primary",
        )

        if start_clicked:
            try:
                with st.spinner("Uploading map and running analysis..."):
                    map_bytes = st.session_state["map_bytes"]
                    map_name = st.session_state["map_name"]
                    files = {
                        "file": (map_name, map_bytes, "image/png")
                    }
                    res = requests.post(
                        f"{API_BASE_URL}/uploadImage", files=files
                    )

                    if res.status_code != 200:
                        st.error(f"Upload map failed: {res.text}")
                        st.stop()

                    res_json = res.json()
                    map_id = res_json.get("image_id")

                    csv_df = st.session_state["csv_df"]
                    column_name = st.session_state["selected_column"]
                    column_values = csv_df[column_name].tolist()

                    ana_payload = {
                        "column_name": column_name,
                        "column_values": column_values,
                    }

                    ana = requests.post(
                        f"{API_BASE_URL}/analyzeMap/{map_id}",
                        json=ana_payload,
                    )

                    if ana.status_code != 200:
                        st.error(
                            f"Analysis failed. Backend response: {ana.text}"
                        )
                        st.stop()

                    result = ana.json().get("analysis", "")
                    st.session_state["analysis"] = result
                    st.session_state["selected_criterion"] = None
                    st.session_state["binning_similarity"] = None

            except Exception as e:
                st.error(f"Error during analysis: {e}")

# Bottom: left / middle / right
bottom_left, bottom_mid, bottom_right = st.columns([1.4, 1.2, 1.2])

analysis_raw = st.session_state.get("analysis")
analysis_json = parse_analysis_json(analysis_raw) if analysis_raw else None

items = evaluate_fields(analysis_json) if isinstance(analysis_json, dict) else []
item_by_label = {it["label"]: it for it in items}

with bottom_mid:
    st.markdown("### ✅ Criteria")

    if not items:
        st.info("Run analysis to see criteria.")
    else:
        map_labels = [
            "Map title", "URL", "Citations",
            "Variables", "Frequency shown",
            "Semantic type", "Background colour",
            "Classification method",
        ]
        legend_labels = [
            "Legend present", "Legend orientation", "Range",
            "No data category", "Explicit 'Other' category",
            "Incomplete info", "Data type", "Contiguity",
            "Number of bins", "Colour scheme", "Colours",
            "Legend placement", "Legend border",
        ]

        st.markdown("**Map info**")
        map_cols = st.columns(4)
        for i, label in enumerate(map_labels):
            if label not in item_by_label:
                continue
            it = item_by_label[label]
            icon = status_to_icon(it["status"])
            col = map_cols[i % 4]
            with col:
                if st.button(f"{icon} {label}", key=f"btn_{label}"):
                    st.session_state["selected_criterion"] = label

        st.markdown("---")
        st.markdown("**Legend**")
        leg_cols = st.columns(4)
        for i, label in enumerate(legend_labels):
            if label not in item_by_label:
                continue
            it = item_by_label[label]
            icon = status_to_icon(it["status"])
            col = leg_cols[i % 4]
            with col:
                if st.button(f"{icon} {label}", key=f"btn_{label}"):
                    st.session_state["selected_criterion"] = label

with bottom_left:
    st.markdown("### 🤖 AI Evaluation")

    sim_dict = st.session_state.get("binning_similarity")
    if sim_dict:
        best_method, best_score = max(sim_dict.items(), key=lambda kv: kv[1])
        st.markdown(
            f"**Most similar binning to the map's Manual Interval**: "
            f"`{best_method}` (similarity = {best_score:.3f})"
        )
        st.markdown("---")

    if not analysis_json:
        st.info("No analysis yet. Run the analysis to see AI feedback.")
    else:
        selected_label = st.session_state.get("selected_criterion")

        if not selected_label or selected_label not in item_by_label:
            overall_text = get_overall_text(analysis_json)
            st.write(overall_text)
        else:
            it = item_by_label[selected_label]
            icon = status_to_icon(it["status"])
            st.markdown(f"#### {icon} {selected_label}")

            value = get_value_by_path(analysis_json, it["path"])
            st.markdown("**Extracted JSON value**")
            st.code(json.dumps(value, indent=2, ensure_ascii=False))

            if it["detail"]:
                st.markdown(f"**Assessment**: {it['detail']}")
            else:
                if it["status"] == "good":
                    st.markdown("**Assessment**: This element meets the guideline.")
                elif it["status"] == "bad":
                    st.markdown("**Assessment**: This element violates the guideline.")
                else:
                    st.markdown(
                        "**Assessment**: This element is not clearly judged from the current information."
                    )

def draw_interval_bar(edges, title, subtitle=None, cmap_name="viridis"):
    edges = np.unique(np.sort(np.array(edges, dtype=float)))
    if len(edges) < 2:
        st.warning(f"{title}: not enough edges to draw intervals.")
        return

    fig, ax = plt.subplots(figsize=(6, 1.0))
    minv, maxv = edges[0], edges[-1]
    width = maxv - minv

    ax.barh(
        y=0,
        width=width,
        left=minv,
        height=0.4,
        color="lightgray",
        edgecolor="none",
        alpha=0.5,
    )

    cmap = plt.get_cmap(cmap_name)
    n_int = len(edges) - 1
    for i in range(n_int):
        left = edges[i]
        right = edges[i + 1]
        c = cmap((i + 0.5) / n_int)
        ax.barh(
            y=0,
            width=right - left,
            left=left,
            height=0.4,
            color=c,
            edgecolor="white",
            linewidth=0.8,
        )

    ax.set_yticks([])
    ax.set_ylim(-0.7, 0.7)
    ax.set_xlim(minv, maxv)
    ax.set_xticks(edges)
    ax.set_xticklabels([f"{e:.2f}" for e in edges], rotation=0, fontsize=8)

    full_title = title
    if subtitle:
        full_title = f"{title} ({subtitle})"
    ax.set_title(full_title, fontsize=10, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    st.pyplot(fig)
    plt.close(fig)


with bottom_right:
    st.markdown("### 📈 Classification Diagram")

    csv_df = st.session_state.get("csv_df")
    selected_column = st.session_state.get("selected_column")

    if (csv_df is None) or (selected_column is None):
        st.info("Upload CSV and choose a numeric column to see diagrams.")
    else:
        if not np.issubdtype(csv_df[selected_column].dtype, np.number):
            st.warning("Selected column is not numeric. Choose a numeric column.")
        else:
            data = csv_df[selected_column].dropna().to_numpy()

            legend_range = None
            legend_bins = None

            if isinstance(analysis_json, dict):
                legend_dict = analysis_json.get("info", {}).get("legend", {})
                legend_range = legend_dict.get("range")
                legend_bins = legend_dict.get("num_bins")

            manual_edges = None

            if legend_range:
                try:
                    # 1-dimension case
                    if all(isinstance(x, (int, float, str)) for x in legend_range):
                        manual_edges = np.array([float(x) for x in legend_range], dtype=float)

                    # 2-dimension case
                    elif all(
                        isinstance(x, (list, tuple)) and len(x) == 2
                        for x in legend_range
                    ):
                        intervals = sorted(
                            [(float(a), float(b)) for (a, b) in legend_range],
                            key=lambda ab: ab[0],
                        )
                        lefts = [iv[0] for iv in intervals]
                        last_right = intervals[-1][1]
                        edges_list = lefts + [last_right]
                        manual_edges = np.array(edges_list, dtype=float)

                    else:
                        manual_edges = None
                except Exception:
                    manual_edges = None

            st.markdown(f"**Data column**: `{selected_column}`")

            # SHow similarity
            show_manual = st.checkbox(
                "Show Similarity (from map legend range)",
                value=True if manual_edges is not None else False,
                disabled=(manual_edges is None),
            )

            # Use legend bin no. if available, else slider
            if legend_bins is not None:
                try:
                    bins = int(legend_bins)
                except Exception:
                    bins = 5
                st.markdown(
                    f"**Number of bins** (from legend): `{bins}`"
                )
            else:
                bins = st.slider(
                    "Number of bins (for data-based methods)",
                    min_value=2,
                    max_value=10,
                    value=5,
                    step=1,
                )

            st.markdown("#### Methods")

            # Sort methods
            method_records = []
            similarity_dict = {}

            if show_manual and manual_edges is not None:
                method_records.append({
                    "name": "Manual Interval (Map Legend)",
                    "edges": manual_edges,
                    "similarity": 1.0,
                    "is_manual": True,
                })
                similarity_dict["Manual Interval (Map Legend)"] = 1.0

            # From binning.py
            for m_name, func in BIN_METHODS.items():
                try:
                    edges = func(data, bins)
                    if len(edges) < 2:
                        continue

                    score = None
                    # Calcaulate similarity
                    if manual_edges is not None and show_manual:
                        score = interval_similarity(manual_edges, edges)
                        if score is not None:
                            similarity_dict[m_name] = float(score)

                    method_records.append({
                        "name": m_name,
                        "edges": edges,
                        "similarity": float(score) if score is not None else None,
                        "is_manual": False,
                    })
                except Exception as e:
                    st.warning(f"{m_name}: error computing bins ({e})")

            def sort_key(rec):
                sim = rec["similarity"]
                return (-sim) if sim is not None else float("inf")

            method_records_sorted = sorted(method_records, key=sort_key)

            for rec in method_records_sorted:
                name = rec["name"]
                edges = rec["edges"]
                sim = rec["similarity"]

                subtitle = None
                if sim is not None:
                    subtitle = f"similarity = {sim:.3f}"

                draw_interval_bar(edges, name, subtitle=subtitle)

            if similarity_dict:
                st.session_state["binning_similarity"] = similarity_dict

                if isinstance(analysis_json, dict):
                    analysis_json.setdefault("binning_similarity", {})
                    analysis_json["binning_similarity"].update(similarity_dict)
            else:
                st.session_state["binning_similarity"] = None

            records_for_table = [
                {"method": name, "score": score}
                for name, score in similarity_dict.items()
            ]
            if manual_edges is not None and records_for_table:
                st.markdown("#### Similarity to Manual Interval")
                sim_df = pd.DataFrame(records_for_table)
                sim_df = sim_df.sort_values("score", ascending=False)
                st.dataframe(
                    sim_df,
                    use_container_width=True,
                    height=240,
                )