# dashboard.py
import numpy as np
import pandas as pd
import streamlit as st

from binning.algorithms import BIN_METHODS
from binning.similarity import interval_similarity
from binning.plotting import draw_interval_bar
from utils.json_utils import try_parse_json_text


def _extract_manual_edges(legend_range):
    manual_edges = None
    if not legend_range:
        return None

    try:
        if all(isinstance(x, (int, float, str)) for x in legend_range):
            manual_edges = np.array([float(x) for x in legend_range], dtype=float)
        elif all(isinstance(x, (list, tuple)) and len(x) == 2 for x in legend_range):
            intervals = sorted([(float(a), float(b)) for (a, b) in legend_range], key=lambda ab: ab[0])
            lefts = [iv[0] for iv in intervals]
            last_right = intervals[-1][1]
            manual_edges = np.array(lefts + [last_right], dtype=float)
    except Exception:
        manual_edges = None

    return manual_edges


def render_classification_diagram(analysis_json: dict):
    st.subheader("Diagram")

    csv_df = st.session_state.get("csv_df")
    selected_column = st.session_state.get("selected_column")
    is_numeric_col = st.session_state.get("is_numeric_column", None)

    if (csv_df is None) or (selected_column is None):
        st.info("Upload CSV and choose a data column to see diagrams.")
        return

    if not is_numeric_col:
        st.info(
            "The selected data column appears to be **categorical**.\n\n"
            "Map-design quality can still be evaluated above in the *AI Evaluation* and *Criteria* sections."
        )
        return

    col_series = csv_df[selected_column]
    data = pd.to_numeric(col_series, errors="coerce").dropna().to_numpy()

    if data.size == 0:
        st.warning("No valid numeric data in this column (all values are NaN/non-numeric).")
        return

    legend_range = None
    legend_bins = None

    # ---------- helpers ----------
    def _get_path(d, path, default=None):
        cur = d
        for p in path.split("."):
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return cur

    def _extract_value_shallow(extract_dict, key_names):
        """Look for extract[k] at the first level, return dict.value if dict."""
        if not isinstance(extract_dict, dict):
            return None
        for k in key_names:
            if k in extract_dict:
                v = extract_dict[k]
                return v.get("value") if isinstance(v, dict) else v
        return None

    # ---------- read legend from analysis_json ----------
    if isinstance(analysis_json, dict):
        # 1) preferred: info.legend.*
        info_legend = (analysis_json.get("info", {}) or {}).get("legend", {}) or {}
        legend_range = info_legend.get("range")
        legend_bins = info_legend.get("num_bins")

        extract = analysis_json.get("extract") or {}

        if legend_bins is None:
            legend_bins = _extract_value_shallow(
                extract,
                ["NUMBER OF BINS", "num_bins", "bins", "number_of_bins", "NUMBER_OF_BINS"],
            )

        if legend_range is None:
            legend_range = _extract_value_shallow(
                extract,
                ["RANGE", "range", "legend_range", "bins_range", "LEGEND_RANGE"],
            )

        # 3) NEW: nested extract.legend.*
        if legend_bins is None:
            v = _get_path(extract, "legend.num_bins.value")
            if v is not None:
                legend_bins = v

        if legend_range is None:
            v = _get_path(extract, "legend.range.value")
            if v is not None:
                legend_range = v

        if isinstance(legend_range, str):
            parsed = try_parse_json_text(legend_range)
            if parsed is not None:
                legend_range = parsed
            else:
                try:
                    import ast
                    legend_range = ast.literal_eval(legend_range)
                except Exception:
                    pass

    manual_edges = _extract_manual_edges(legend_range)

    if legend_bins is None:
        st.warning(
            "Cannot render binning diagram because legend bin count is missing.\n\n"
            "Expected one of:\n"
            "- `info.legend.num_bins`\n"
            "- `extract.legend.num_bins.value`\n"
            "- `extract['NUMBER OF BINS'].value` (legacy)\n"
        )
        return

    try:
        bins = int(float(legend_bins))
        if bins < 2:
            raise ValueError("num_bins must be >= 2")
    except Exception:
        st.warning(f"Cannot render binning diagram because bin count is invalid: {legend_bins!r}")
        return

    st.markdown(f"**Number of bins** (from map legend): `{bins}`")

    if manual_edges is None:
        st.warning(
            "Cannot compute similarity because legend range is missing/invalid.\n\n"
            "Expected one of:\n"
            "- `info.legend.range`\n"
            "- `extract.legend.range.value`\n"
            "- `extract['RANGE'].value` (legacy)\n\n"
            "Supported formats:\n"
            "- edges like `[6, 11, 16, ...]`\n"
            "- intervals like `[[6, 10.99], [11, 15.99], ...]`"
        )
        return

    method_records = []
    similarity_dict = {}

    for m_name, func in BIN_METHODS.items():
        try:
            edges = func(data, bins)
            if edges is None:
                continue
            edges = np.asarray(edges, dtype=float)
            if len(edges) < 2:
                continue

            score = interval_similarity(manual_edges, edges)
            score_f = float(score) if score is not None else None

            method_records.append({"name": m_name, "edges": edges, "similarity": score_f})
            if score_f is not None:
                similarity_dict[m_name] = score_f

        except Exception as e:
            st.warning(f"{m_name}: error computing bins ({e})")

    if not method_records:
        st.warning("No binning methods produced edges.")
        return

    method_records_sorted = sorted(
        method_records,
        key=lambda rec: (rec["similarity"] is None, -(rec["similarity"] or -1e18)),
    )

    USE_FREQUENCY_HEIGHT = True
    for rec in method_records_sorted:
        subtitle = f"similarity = {rec['similarity']:.3f}" if rec["similarity"] is not None else "similarity = N/A"
        draw_interval_bar(
            rec["edges"],
            rec["name"],
            subtitle=subtitle,
            data=data,
            use_frequency_height=USE_FREQUENCY_HEIGHT,
        )

    st.session_state["binning_similarity"] = similarity_dict or None
    if isinstance(analysis_json, dict):
        analysis_json.setdefault("binning_similarity", {})
        analysis_json["binning_similarity"].update(similarity_dict)
