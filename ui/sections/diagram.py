import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from binning.algorithms import BIN_METHODS
from binning.similarity import interval_similarity
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


def _counts_per_bin(data: np.ndarray, edges: np.ndarray) -> np.ndarray:

    lefts = edges[:-1]
    rights = edges[1:]
    x = np.asarray(data, dtype=float)
    x = x[np.isfinite(x)]
    counts = np.zeros(len(lefts), dtype=int)

    for i, (a, b) in enumerate(zip(lefts, rights)):
        if i < len(lefts) - 1:
            counts[i] = int(np.sum((x >= a) & (x < b)))
        else:
            counts[i] = int(np.sum((x >= a) & (x <= b)))
    return counts


def _format_ticks_from_edges(edges: np.ndarray, precision: int = 2):
    def fmt(v: float) -> str:
        s = f"{v:.{precision}f}"
        return s.rstrip("0").rstrip(".")

    tickvals = [float(v) for v in edges.tolist()]
    ticktext = [fmt(v) for v in tickvals]
    return tickvals, ticktext

def draw_binning_diagram_plotly(
    edges,
    method_name: str,
    similarity: float | None,
    data: np.ndarray,
    tick_precision: int = 2,
    height: int = 190,
):
    edges = np.asarray(edges, dtype=float).reshape(-1)
    edges = edges[np.isfinite(edges)]
    edges = np.unique(edges)

    if edges.size < 2:
        st.warning(f"{method_name}: invalid edges (need >=2 unique finite edges).")
        return

    widths = np.diff(edges)
    if np.any(widths <= 0):
        st.warning(f"{method_name}: invalid edges (must be strictly increasing).")
        return

    x = np.asarray(data, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        st.warning("No valid numeric data to plot.")
        return

    counts = _counts_per_bin(x, edges)
    total = int(x.size)
    shares = counts / max(total, 1) * 100.0

    lefts = edges[:-1]
    rights = edges[1:]
    centers = (lefts + rights) / 2.0

    if similarity is None:
        title_text = f"{method_name} (Similarity: N/A)"
    else:
        title_text = f"{method_name} (Similarity: {similarity * 100:.0f}%)"

    colors = [
        "#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2",
        "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC",
    ]

    ymax = int(max(counts.max(), 1))

    fig = go.Figure()

    for i, (a, b, c, w) in enumerate(zip(lefts, rights, centers, widths)):
        is_last = (i == len(lefts) - 1)
        range_text = (
            f"[{a:.{tick_precision}f}, {b:.{tick_precision}f}]"
            if is_last
            else f"[{a:.{tick_precision}f}, {b:.{tick_precision}f})"
        )

        hover = (
            f"<b>{method_name}</b><br>"
            f"Range: {range_text}<br>"
            f"Count: {counts[i]}<br>"
            f"Share: {shares[i]:.1f}%<br>"
            f"Total: {total}"
            "<extra></extra>"
        )

        fig.add_trace(
            go.Bar(
                x=[float(c)],
                y=[ymax],
                width=[float(w)],
                marker=dict(color="rgba(0,0,0,0)", line=dict(width=0)),
                opacity=0.0,
                hovertemplate=hover,
                showlegend=False,
            )
        )

    for i, (c, w) in enumerate(zip(centers, widths)):
        fig.add_trace(
            go.Bar(
                x=[float(c)],
                y=[int(counts[i])],
                width=[float(w)],
                marker=dict(color=colors[i % len(colors)], line=dict(width=0)),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    tickvals, ticktext = _format_ticks_from_edges(edges, precision=tick_precision)

    fig.update_layout(
        title=dict(text=title_text, x=0.0, xanchor="left"),
        height=height,
        margin=dict(l=25, r=20, t=58, b=50),
        barmode="overlay",

        hovermode="closest",

        hoverlabel=dict(namelength=0),
        xaxis=dict(
            title="",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            range=[float(edges.min()), float(edges.max())],
            automargin=True,
            zeroline=False,
        ),
        yaxis=dict(
            title="Count",
            rangemode="tozero",
            range=[0, ymax],
            automargin=True,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=False,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
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

    if isinstance(analysis_json, dict):
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

    for rec in method_records_sorted:
        draw_binning_diagram_plotly(
            rec["edges"],
            method_name=rec["name"],
            similarity=rec["similarity"],
            data=data,
            tick_precision=2,
            height=160,
        )

    st.session_state["binning_similarity"] = similarity_dict or None
    if isinstance(analysis_json, dict):
        analysis_json.setdefault("binning_similarity", {})
        analysis_json["binning_similarity"].update(similarity_dict)