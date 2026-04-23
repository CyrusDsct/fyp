import json
from typing import Any


CLASSIFICATION_METHODS = {
    "Unclassed",
    "Defined Interval",
    "Equal Interval",
    "Pretty Breaks",
    "Geometric",
    "Geometric Interval",
    "Exponential",
    "Manual Interval",
    "Manual Intervals",
    "Quantile",
    "Percentile",
    "Box Plot",
    "Boxplot Interquartile Range",
    "Standard Deviation",
    "Maximum Breaks",
    "Natural Breaks",
    "CK-Means",
    "Head Tail Breaks",
    "Head/Tail Breaks",
    "Resiliency",
}


def parse_analysis_json(raw: str):
    if not raw:
        return None

    try:
        return json.loads(raw)
    except Exception:
        pass

    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
    except ValueError:
        return None

    try:
        return json.loads(raw[start:end])
    except Exception:
        return None


def get_overall_text(ana_dict: dict) -> str:
    if not isinstance(ana_dict, dict):
        return "No structured JSON found in analysis."

    info = ana_dict.get("info", {}) or {}
    explanation = ana_dict.get("explanation")
    map_quality = ana_dict.get("map_quality")

    parts = []
    if explanation:
        parts.append(f"**Map explanation**\n\n{explanation}")
    if map_quality:
        parts.append(f"**Map quality / reasoning**\n\n{map_quality}")

    if parts:
        return "\n\n---\n\n".join(parts)

    title = info.get("map_title")
    if title:
        return f"**Map title**: {title}"
    return "No explanation/map_quality fields found in JSON."


def make_item(label, key_path, value, status, detail=None):
    return {
        "label": label,
        "path": key_path,
        "value": value,
        "status": status,
        "detail": detail or "",
    }


def status_to_icon(status: str):
    if status == "good":
        return "GOOD"
    if status == "bad":
        return "BAD"
    return "UNKNOWN"


def get_value_by_path(analysis_json, path):
    current = analysis_json
    try:
        for part in path:
            current = current[part]
        return current
    except Exception:
        return None


def _append(items: list[dict[str, Any]], label: str, path, value, status: str, detail: str | None = None):
    items.append(make_item(label, path, value, status, detail))


def evaluate_fields(analysis_json: dict):
    if not isinstance(analysis_json, dict):
        return []

    items = []
    info = analysis_json.get("info", {}) or {}
    legend = info.get("legend", {}) or {}

    map_title = info.get("map_title")
    if isinstance(map_title, str) and map_title.strip():
        _append(items, "Map title", ("info", "map_title"), map_title, "good")
    else:
        _append(items, "Map title", ("info", "map_title"), map_title, "bad", "No map title found.")

    url = info.get("url")
    if not url or url in {"None", "Not Applicable", "not applicable"}:
        _append(items, "URL", ("info", "url"), url, "bad", "No valid source URL.")
    else:
        _append(items, "URL", ("info", "url"), url, "good")

    citations = info.get("citations")
    if isinstance(citations, str) and citations.strip():
        _append(items, "Citations", ("info", "citations"), citations, "good")
    else:
        _append(items, "Citations", ("info", "citations"), citations, "unknown", "No explicit citation text detected.")

    has_legend = legend.get("has_legend")
    if has_legend == "yes":
        _append(items, "Legend present", ("info", "legend", "has_legend"), has_legend, "good")
    elif has_legend == "no":
        _append(
            items,
            "Legend present",
            ("info", "legend", "has_legend"),
            has_legend,
            "bad",
            "Choropleth without legend.",
        )
    else:
        _append(items, "Legend present", ("info", "legend", "has_legend"), has_legend, "unknown")

    orientation = legend.get("orientation")
    if orientation in {"horizontal", "vertical", "other", "not applicable"}:
        _append(items, "Legend orientation", ("info", "legend", "orientation"), orientation, "unknown")
    else:
        _append(
            items,
            "Legend orientation",
            ("info", "legend", "orientation"),
            orientation,
            "unknown",
            "Orientation not clearly identified.",
        )

    legend_range = legend.get("range")
    if legend_range is None:
        _append(items, "Range", ("info", "legend", "range"), legend_range, "bad", "No range information for legend.")
    elif isinstance(legend_range, list) and legend_range:
        _append(items, "Range", ("info", "legend", "range"), legend_range, "good")
    else:
        _append(items, "Range", ("info", "legend", "range"), legend_range, "unknown")

    no_data = legend.get("no_data")
    if no_data == "yes":
        _append(items, "No data category", ("info", "legend", "no_data"), no_data, "good")
    elif no_data == "no":
        _append(
            items,
            "No data category",
            ("info", "legend", "no_data"),
            no_data,
            "bad",
            "No-data regions may be ambiguous.",
        )
    else:
        _append(items, "No data category", ("info", "legend", "no_data"), no_data, "unknown")

    explicit_other = legend.get("explicit_other")
    if explicit_other == "yes":
        _append(items, "Explicit 'Other' category", ("info", "legend", "explicit_other"), explicit_other, "good")
    elif explicit_other == "no":
        _append(
            items,
            "Explicit 'Other' category",
            ("info", "legend", "explicit_other"),
            explicit_other,
            "unknown",
            "May not be needed depending on semantic type.",
        )
    else:
        _append(items, "Explicit 'Other' category", ("info", "legend", "explicit_other"), explicit_other, "unknown")

    incomplete_info = legend.get("incomplete_info")
    if incomplete_info == "no":
        _append(items, "Incomplete info", ("info", "legend", "incomplete_info"), incomplete_info, "good")
    elif incomplete_info == "yes":
        _append(
            items,
            "Incomplete info",
            ("info", "legend", "incomplete_info"),
            incomplete_info,
            "bad",
            "Legend is missing some colours/data.",
        )
    else:
        _append(items, "Incomplete info", ("info", "legend", "incomplete_info"), incomplete_info, "unknown")

    data_type = legend.get("data_type")
    if data_type in {"nominal", "ordinal", "interval", "ratio"}:
        _append(items, "Data type", ("info", "legend", "data_type"), data_type, "good")
    else:
        _append(
            items,
            "Data type",
            ("info", "legend", "data_type"),
            data_type,
            "bad",
            "Data type not clearly identified.",
        )

    contiguity = legend.get("contiguity")
    if contiguity in {"yes", "no", "not applicable"}:
        _append(items, "Contiguity", ("info", "legend", "contiguity"), contiguity, "unknown")
    else:
        _append(
            items,
            "Contiguity",
            ("info", "legend", "contiguity"),
            contiguity,
            "unknown",
            "Contiguity not clearly specified.",
        )

    num_bins = legend.get("num_bins")
    if isinstance(num_bins, int):
        if 3 <= num_bins <= 7:
            _append(items, "Number of bins", ("info", "legend", "num_bins"), num_bins, "good")
        else:
            _append(
                items,
                "Number of bins",
                ("info", "legend", "num_bins"),
                num_bins,
                "bad",
                "Too few or too many bins for clear interpretation.",
            )
    elif isinstance(num_bins, str) and num_bins.lower() == "not applicable":
        _append(items, "Number of bins", ("info", "legend", "num_bins"), num_bins, "unknown")
    else:
        _append(items, "Number of bins", ("info", "legend", "num_bins"), num_bins, "unknown")

    colour_scheme = legend.get("colour_scheme")
    if colour_scheme in {
        "Sequential Single-hue",
        "Sequential Multi-hue",
        "Categorical",
        "Diverging",
        "Cyclic",
        "Other",
        "Not Applicable",
    }:
        _append(items, "Colour scheme", ("info", "legend", "colour_scheme"), colour_scheme, "good")
    else:
        _append(
            items,
            "Colour scheme",
            ("info", "legend", "colour_scheme"),
            colour_scheme,
            "bad",
            "Colour scheme not identified.",
        )

    colours = legend.get("colours")
    if colours:
        _append(items, "Colours", ("info", "legend", "colours"), colours, "unknown")
    else:
        _append(
            items,
            "Colours",
            ("info", "legend", "colours"),
            colours,
            "unknown",
            "No explicit list of legend colours.",
        )

    placement = legend.get("placement")
    valid_placements = {
        "top left",
        "top center",
        "top right",
        "middle left",
        "center",
        "middle right",
        "bottom left",
        "bottom center",
        "bottom right",
    }
    if placement in valid_placements:
        if placement == "center":
            _append(
                items,
                "Legend placement",
                ("info", "legend", "placement"),
                placement,
                "bad",
                "Legend centered may obscure map content.",
            )
        else:
            _append(items, "Legend placement", ("info", "legend", "placement"), placement, "good")
    else:
        _append(items, "Legend placement", ("info", "legend", "placement"), placement, "unknown")

    border = legend.get("border")
    if border in {"yes", "no", "not applicable"}:
        _append(items, "Legend border", ("info", "legend", "border"), border, "unknown")
    else:
        _append(
            items,
            "Legend border",
            ("info", "legend", "border"),
            border,
            "unknown",
            "Border information not clear.",
        )

    variables = info.get("variables")
    if isinstance(variables, int) and variables >= 1:
        if variables == 1:
            _append(items, "Variables", ("info", "variables"), variables, "good")
        else:
            _append(items, "Variables", ("info", "variables"), variables, "unknown", "Multiple variables may increase complexity.")
    else:
        _append(items, "Variables", ("info", "variables"), variables, "bad", "Number of variables not clearly identified.")

    frequency = info.get("frequency")
    if frequency in {"yes", "no"}:
        _append(items, "Frequency shown", ("info", "frequency"), frequency, "unknown")
    else:
        _append(items, "Frequency shown", ("info", "frequency"), frequency, "unknown", "Frequency information not clear.")

    semantic_type = info.get("semantic_type")
    if isinstance(semantic_type, str) and semantic_type.strip():
        _append(items, "Semantic type", ("info", "semantic_type"), semantic_type, "good")
    else:
        _append(
            items,
            "Semantic type",
            ("info", "semantic_type"),
            semantic_type,
            "bad",
            "What the data represents is unclear.",
        )

    background_colour = info.get("bgcolour")
    if background_colour:
        _append(items, "Background colour", ("info", "bgcolour"), background_colour, "unknown")
    else:
        _append(
            items,
            "Background colour",
            ("info", "bgcolour"),
            background_colour,
            "unknown",
            "Background colour not identified.",
        )

    classification = info.get("classification")
    if classification in CLASSIFICATION_METHODS:
        _append(items, "Classification method", ("info", "classification"), classification, "neutral")
    else:
        _append(
            items,
            "Classification method",
            ("info", "classification"),
            classification or "Manual Interval",
            "neutral",
            "Classification method unclear.",
        )

    return items
