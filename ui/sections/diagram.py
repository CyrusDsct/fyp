import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from binning.algorithms import BIN_METHODS
from binning.similarity import composite_similarity_details
from utils.data_utils import coerce_numeric_series
from utils.json_utils import try_parse_json_text


EXCLUDED_COMPARISON_METHODS = {"Defined Interval"}


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
    title_text: str | None = None,
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

    if title_text is None:
        if similarity is None:
            title_text = f"{method_name}"
        else:
            title_text = f"{method_name} ({similarity * 100:.0f}% similarity)"

    colors = [
        "#4C78A8",
        "#F58518",
        "#54A24B",
        "#E45756",
        "#72B7B2",
        "#B279A2",
        "#FF9DA6",
        "#9D755D",
        "#BAB0AC",
    ]

    ymax = int(max(counts.max(), 1))

    fig = go.Figure()

    for i, (a, b, c, w) in enumerate(zip(lefts, rights, centers, widths)):
        is_last = i == len(lefts) - 1
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
        title=dict(text=(title_text or ""), x=0.0, xanchor="left"),
        height=height,
        margin=dict(l=18, r=10, t=(38 if title_text else 10), b=2),
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

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _get_path(data, path, default=None):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _extract_value_shallow(extract_dict, key_names):
    if not isinstance(extract_dict, dict):
        return None
    for key_name in key_names:
        if key_name in extract_dict:
            value = extract_dict[key_name]
            return value.get("value") if isinstance(value, dict) else value
    return None


def _extract_classification_method(analysis_json: dict) -> str:
    paths = [
        "inferred_interpretation.map.classification_method.value",
        "facts.inferred_interpretation.map.classification_method.value",
        "info.classification",
    ]
    for path in paths:
        value = _get_path(analysis_json, path)
        if value:
            return str(value)
    return "Unknown"


def _extract_binning_inputs(analysis_json: dict):
    data_bytes = st.session_state.get("data_bytes")
    csv_df = st.session_state.get("csv_df")
    selected_column = st.session_state.get("selected_column")
    is_numeric_col = st.session_state.get("is_numeric_column", None)

    if (not data_bytes) or (csv_df is None) or (selected_column is None):
        return None, None, None, "Upload CSV and choose a data column to see binning results."

    if not is_numeric_col:
        return None, None, None, "The selected data column is categorical, so binning comparison is unavailable."

    if selected_column not in csv_df.columns:
        return None, None, None, "The selected data column is no longer available. Please reselect a CSV column."

    col_series = csv_df[selected_column]
    data = coerce_numeric_series(col_series).dropna().to_numpy()
    if data.size == 0:
        return None, None, None, "No valid numeric data is available in the selected column."

    legend_range = None
    legend_bins = None

    if isinstance(analysis_json, dict):
        metadata_map = _get_path(analysis_json, "facts.metadata.map", {}) or {}

        legend_bins = _extract_value_shallow(
            metadata_map,
            ["number_of_bins", "num_bins", "NUMBER OF BINS", "NUMBER_OF_BINS", "bins"],
        )
        legend_range = _extract_value_shallow(
            metadata_map,
            ["data_breaks", "range", "RANGE", "legend_range", "LEGEND_RANGE"],
        )

        extract = analysis_json.get("extract") or {}
        if legend_bins is None:
            legend_bins = _extract_value_shallow(
                extract,
                ["NUMBER OF BINS", "num_bins", "bins", "number_of_bins", "NUMBER_OF_BINS"],
            )
        if legend_range is None:
            legend_range = _extract_value_shallow(
                extract,
                ["RANGE", "range", "legend_range", "bins_range", "LEGEND_RANGE", "data_breaks"],
            )

        if legend_bins is None:
            legend_bins = _get_path(extract, "legend.num_bins.value")
        if legend_range is None:
            legend_range = _get_path(extract, "legend.range.value")

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
        return None, None, None, "Legend bin count is missing from the analysis output."
    try:
        bins = int(float(legend_bins))
        if bins < 2:
            raise ValueError("num_bins must be >= 2")
    except Exception:
        return None, None, None, f"Legend bin count is invalid: {legend_bins!r}"

    if manual_edges is None:
        return None, None, None, "Legend data breaks are missing or invalid, so similarity cannot be computed."

    return data, bins, manual_edges, None


def _extract_binning_status(analysis_json: dict) -> dict:
    data_bytes = st.session_state.get("data_bytes")
    csv_df = st.session_state.get("csv_df")
    selected_column = st.session_state.get("selected_column")
    is_numeric_col = st.session_state.get("is_numeric_column", None)

    legend_range = None
    legend_bins = None
    if isinstance(analysis_json, dict):
        metadata_map = _get_path(analysis_json, "facts.metadata.map", {}) or {}

        legend_bins = _extract_value_shallow(
            metadata_map,
            ["number_of_bins", "num_bins", "NUMBER OF BINS", "NUMBER_OF_BINS", "bins"],
        )
        legend_range = _extract_value_shallow(
            metadata_map,
            ["data_breaks", "range", "RANGE", "legend_range", "LEGEND_RANGE"],
        )

        extract = analysis_json.get("extract") or {}
        if legend_bins is None:
            legend_bins = _extract_value_shallow(
                extract,
                ["NUMBER OF BINS", "num_bins", "bins", "number_of_bins", "NUMBER_OF_BINS"],
            )
        if legend_range is None:
            legend_range = _extract_value_shallow(
                extract,
                ["RANGE", "range", "legend_range", "bins_range", "LEGEND_RANGE", "data_breaks"],
            )

        if legend_bins is None:
            legend_bins = _get_path(extract, "legend.num_bins.value")
        if legend_range is None:
            legend_range = _get_path(extract, "legend.range.value")

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

    numeric_value_count = 0
    if csv_df is not None and selected_column in getattr(csv_df, "columns", []):
        try:
            numeric_value_count = int(coerce_numeric_series(csv_df[selected_column]).dropna().shape[0])
        except Exception:
            numeric_value_count = 0

    return {
        "has_csv": bool(data_bytes) and csv_df is not None,
        "selected_column": selected_column,
        "is_numeric_column": bool(is_numeric_col),
        "numeric_value_count": numeric_value_count,
        "legend_bins": legend_bins,
        "legend_breaks_raw": legend_range,
        "legend_breaks_parsed": _extract_manual_edges(legend_range),
    }


def render_binning_status(analysis_json: dict) -> None:
    status = _extract_binning_status(analysis_json)

    st.markdown("**Binning prerequisites**")
    st.markdown(f"CSV uploaded: `{ 'yes' if status['has_csv'] else 'no' }`")
    st.markdown(f"Selected column: `{status['selected_column'] or 'none'}`")
    st.markdown(f"Numeric column: `{ 'yes' if status['is_numeric_column'] else 'no' }`")
    st.markdown(f"Valid numeric values: `{status['numeric_value_count']}`")
    st.markdown(f"Legend bin count extracted: `{status['legend_bins'] if status['legend_bins'] is not None else 'missing'}`")
    st.markdown(
        f"Legend breaks extracted: `{ 'yes' if status['legend_breaks_parsed'] is not None else 'no' }`"
    )
    st.markdown('<div class="binning-gap-collapser"></div>', unsafe_allow_html=True)


def _compute_binning_diagnostics(analysis_json: dict):
    data, bins, manual_edges, error = _extract_binning_inputs(analysis_json)
    if error:
        return {"error": error}

    method_records = []
    similarity_dict = {}

    for method_name, func in BIN_METHODS.items():
        if method_name in EXCLUDED_COMPARISON_METHODS:
            continue

        try:
            edges = func(data, bins)
            if edges is None:
                continue
            edges = np.asarray(edges, dtype=float)
            if len(edges) < 2:
                continue

            similarity_details = composite_similarity_details(manual_edges, edges, data)
            score_value = float(similarity_details["similarity"]) if similarity_details is not None else None
            method_records.append(
                {
                    "name": method_name,
                    "edges": edges,
                    "similarity": score_value,
                    "similarity_details": similarity_details,
                }
            )
            if score_value is not None:
                similarity_dict[method_name] = score_value
        except Exception as exc:
            method_records.append(
                {
                    "name": method_name,
                    "edges": None,
                    "similarity": None,
                    "error": str(exc),
                }
            )

    method_records_sorted = sorted(
        method_records,
        key=lambda record: (record.get("similarity") is None, -(record.get("similarity") or -1e18), record["name"]),
    )

    st.session_state["binning_similarity"] = similarity_dict or None
    if isinstance(analysis_json, dict):
        analysis_json.setdefault("binning_similarity", {})
        analysis_json["binning_similarity"].update(similarity_dict)

    return {
        "data": data,
        "bins": bins,
        "manual_edges": np.asarray(manual_edges, dtype=float),
        "classification_method": _extract_classification_method(analysis_json),
        "method_records_sorted": method_records_sorted,
        "similarity_dict": similarity_dict,
    }


def build_binning_diagnostics(analysis_json: dict):
    cached = st.session_state.get("_binning_diagnostics_cache")
    if cached is not None:
        return cached
    result = _compute_binning_diagnostics(analysis_json)
    st.session_state["_binning_diagnostics_cache"] = result
    return result


def _format_edge_list(edges) -> str:
    return ", ".join(f"{float(edge):.2f}".rstrip("0").rstrip(".") for edge in edges)


def _format_method_label(name: str, similarity: float | None) -> str:
    if similarity is None:
        return name
    return f"{name} (Similarity: {similarity * 100:.1f}%)"


def _tooltip_metric(label: str, value: str, tooltip: str):
    label_html = html.escape(label)
    value_html = html.escape(value)
    tooltip_html = html.escape(tooltip)
    st.markdown(
        (
            '<div class="similarity-metric-row">'
            f'<span class="similarity-metric-label">{label_html}</span>'
            f'<span class="similarity-tooltip" title="{tooltip_html}">?</span>'
            f'<span class="similarity-metric-value">= <code>{value_html}</code></span>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_similarity_explainer(manual_edges, auto_edges, similarity: float | None, details: dict | None = None):
    st.markdown(
        "Similarity combines interval structure with data-count distribution. "
        "The data-count part compares bin heights using histogram-density overlap."
    )
    if similarity is None or not details:
        st.write("This method did not produce a valid similarity score.")
        return

    manual_edges = np.asarray(manual_edges, dtype=float)
    auto_edges = np.asarray(auto_edges, dtype=float)
    interval = details.get("interval") or {}
    frequency = details.get("frequency") or {}

    manual_norm = np.asarray(interval.get("manual_norm", []), dtype=float)
    auto_norm = np.asarray(interval.get("auto_norm", []), dtype=float)
    manual_widths = np.asarray(interval.get("manual_widths", []), dtype=float)
    auto_widths = np.asarray(interval.get("auto_widths", []), dtype=float)
    avg_width_error = float(interval.get("width_error", 0.0))
    avg_edge_error = float(interval.get("edge_error", 0.0))
    bin_count_penalty = float(interval.get("bin_count_penalty", 0.0))
    frequency_score = float(details.get("frequency_similarity", 0.0))
    manual_counts = np.asarray(frequency.get("manual_counts", []), dtype=float)
    auto_counts = np.asarray(frequency.get("auto_counts", []), dtype=float)
    manual_shares = np.asarray(frequency.get("manual_shares", []), dtype=float)
    auto_shares = np.asarray(frequency.get("auto_shares", []), dtype=float)

    st.markdown("**Step 1. Extract the bin edges from the uploaded map and this method.**")
    st.markdown(f"Uploaded map edges: `{_format_edge_list(manual_edges)}`")
    st.markdown(f"This method edges: `{_format_edge_list(auto_edges)}`")

    st.markdown("**Step 2. Normalize both edge sets onto a 0 to 1 scale.**")
    st.markdown(f"Uploaded normalized edges: `{_format_edge_list(manual_norm)}`")
    st.markdown(f"This method normalized edges: `{_format_edge_list(auto_norm)}`")

    st.markdown("**Step 3. Compare bin widths and internal edge positions.**")
    st.markdown(f"Uploaded normalized bin widths: `{_format_edge_list(manual_widths)}`")
    st.markdown(f"This method normalized bin widths: `{_format_edge_list(auto_widths)}`")
    _tooltip_metric(
        "Average width error",
        f"{avg_width_error:.3f}",
        "Average absolute difference between the uploaded map's normalized bin widths and this method's normalized bin widths. Lower is better.",
    )
    _tooltip_metric(
        "Average internal-edge error",
        f"{avg_edge_error:.3f}",
        "Average absolute difference between the internal break positions after both edge sets are normalized to 0-1. Lower means the breaks occur in more similar positions.",
    )
    _tooltip_metric(
        "Bin-count penalty",
        f"{bin_count_penalty:.3f}",
        "Penalty for using a different number of bins from the uploaded map. 1 means the bin counts match; lower values mean the method has more or fewer bins.",
    )

    st.markdown("**Step 4. Compare bin heights from data counts.**")
    st.markdown(f"Uploaded bin counts: `{_format_edge_list(manual_counts)}`")
    st.markdown(f"This method bin counts: `{_format_edge_list(auto_counts)}`")
    st.markdown(f"Uploaded count shares: `{_format_edge_list(manual_shares)}`")
    st.markdown(f"This method count shares: `{_format_edge_list(auto_shares)}`")
    st.markdown(
        "Frequency similarity is the overlapping area between the two bin-height distributions: "
        "`integral(min(uploaded_density, method_density))`."
    )
    _tooltip_metric(
        "Frequency similarity",
        f"{frequency_score:.3f}",
        "Overlap between the uploaded map's bin-height distribution and this method's bin-height distribution. Higher means the methods place similar shares of data into bins.",
    )

    st.markdown("**Step 5. Final similarity score.**")
    _tooltip_metric(
        "Final similarity score",
        f"{similarity * 100:.1f}%",
        "Weighted final score: 45% interval similarity and 55% frequency similarity. Higher means this method is more similar to the uploaded map's legend breaks and data distribution.",
    )


def render_binning_method_rankings(diagnostics: dict, chart_height: int = 150):
    method_records_sorted = diagnostics.get("method_records_sorted") or []
    if not method_records_sorted:
        st.info("No binning methods were available for comparison.")
        return

    for index, record in enumerate(method_records_sorted):
        if record.get("error"):
            st.caption(f"Could not compute this method: {record['error']}")
            st.markdown("<hr>", unsafe_allow_html=True)
            continue

        st.markdown(
            f'<div class="binning-method-name">{_format_method_label(record["name"], record.get("similarity"))}</div>',
            unsafe_allow_html=True,
        )
        draw_binning_diagram_plotly(
            record["edges"],
            method_name=record["name"],
            similarity=record.get("similarity"),
            data=diagnostics["data"],
            tick_precision=2,
            height=chart_height,
            title_text="",
        )

        with st.expander("Show calculation"):
            render_similarity_explainer(
                diagnostics["manual_edges"],
                record["edges"],
                record.get("similarity"),
                record.get("similarity_details"),
            )
        if index < len(method_records_sorted) - 1:
            st.markdown('<div class="binning-method-divider"></div>', unsafe_allow_html=True)


def render_binning_details(analysis_json: dict):
    diagnostics = build_binning_diagnostics(analysis_json)
    if diagnostics.get("error"):
        render_binning_status(analysis_json)
        st.warning("Binning comparison is unavailable for this analysis.")
        st.caption(diagnostics["error"])
        return

    st.markdown('<div class="binning-heading uploaded-heading">The uploaded map is binned as:</div>', unsafe_allow_html=True)
    draw_binning_diagram_plotly(
        diagnostics["manual_edges"],
        method_name="Uploaded map",
        similarity=None,
        data=diagnostics["data"],
        tick_precision=2,
        height=144,
        title_text="",
    )
    st.markdown('<div class="binning-gap-collapser"></div>', unsafe_allow_html=True)
    st.markdown('<div class="binning-heading tight-top larger">Other similar binning methods include...</div>', unsafe_allow_html=True)
    st.markdown('<div class="binning-method-list-top"></div>', unsafe_allow_html=True)
    render_binning_method_rankings(diagnostics, chart_height=138)


def render_classification_diagram(analysis_json: dict):
    diagnostics = build_binning_diagnostics(analysis_json)
    if diagnostics.get("error"):
        st.info(diagnostics["error"])
        return

    st.subheader("Binning related")
    render_binning_method_rankings(diagnostics, chart_height=155)
