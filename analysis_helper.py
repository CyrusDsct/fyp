import json

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
        snippet = raw[start:end]
        return json.loads(snippet)
    except Exception:
        return None


def get_overall_text(ana_dict: dict) -> str:
    if not isinstance(ana_dict, dict):
        return "No structured JSON found in analysis."

    info = ana_dict.get("info", {})
    explanation = ana_dict.get("explanation")
    map_quality = ana_dict.get("map_quality")

    parts = []
    if explanation:
        parts.append(f"**Map explanation**\n\n{explanation}")
    if map_quality:
        parts.append(f"**Map quality / reasoning**\n\n{map_quality}")

    if not parts:
        title = info.get("map_title")
        if title:
            parts.append(f"**Map title**: {title}")
        else:
            parts.append("No explanation/map_quality fields found in JSON.")

    return "\n\n---\n\n".join(parts)


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
        return "🟢"
    if status == "bad":
        return "❌"
    return "⚠️"


def get_value_by_path(analysis_json, path):
    cur = analysis_json
    try:
        for p in path:
            cur = cur[p]
        return cur
    except Exception:
        return None


def evaluate_fields(analysis_json: dict):
    items = []
    if not isinstance(analysis_json, dict):
        return items

    info = analysis_json.get("info", {}) or {}
    legend = info.get("legend", {}) or {}

    # MAP TITLE
    map_title = info.get("map_title")
    if map_title and isinstance(map_title, str) and map_title.strip():
        items.append(make_item("Map title", ("info", "map_title"),
                               map_title, "good"))
    else:
        items.append(make_item("Map title", ("info", "map_title"),
                               map_title, "bad", "No map title found."))

    # URL
    url = info.get("url")
    if not url or url in ["None", "Not Applicable", "not applicable"]:
        items.append(make_item("URL", ("info", "url"),
                               url, "bad", "No valid source URL."))
    else:
        items.append(make_item("URL", ("info", "url"), url, "good"))

    # CITATIONS
    citations = info.get("citations")
    if citations and isinstance(citations, str) and citations.strip():
        items.append(make_item("Citations", ("info", "citations"),
                               citations, "good"))
    else:
        items.append(make_item("Citations", ("info", "citations"),
                               citations, "unknown",
                               "No explicit citation text detected."))

    # HAS LEGEND 
    legend_dict = legend
    has_legend = legend_dict.get("has_legend")
    if has_legend == "yes":
        items.append(make_item("Legend present",
                               ("info", "legend", "has_legend"),
                               has_legend, "good"))
    elif has_legend == "no":
        items.append(make_item("Legend present",
                               ("info", "legend", "has_legend"),
                               has_legend, "bad",
                               "Choropleth without legend."))
    else:
        items.append(make_item("Legend present",
                               ("info", "legend", "has_legend"),
                               has_legend, "unknown"))

    # LEGEND ORIENTATION
    orient = legend_dict.get("orientation")
    if orient in ["horizontal", "vertical", "other", "not applicable"]:
        items.append(make_item("Legend orientation",
                               ("info", "legend", "orientation"),
                               orient, "unknown"))
    else:
        items.append(make_item("Legend orientation",
                               ("info", "legend", "orientation"),
                               orient, "unknown",
                               "Orientation not clearly identified."))

    # RANGE
    legend_range = legend_dict.get("range")
    if legend_range is None:
        status, detail = "bad", "No range information for legend."
    else:
        status, detail = "unknown", None
        try:
            if isinstance(legend_range, list) and legend_range:
                status = "good"
        except Exception:
            status = "unknown"
    items.append(make_item("Range", ("info", "legend", "range"),
                           legend_range, status, detail))

    # NO DATA
    no_data = legend_dict.get("no_data")
    if no_data == "yes":
        items.append(make_item("No data category",
                               ("info", "legend", "no_data"),
                               no_data, "good"))
    elif no_data == "no":
        items.append(make_item("No data category",
                               ("info", "legend", "no_data"),
                               no_data, "bad",
                               "No-data regions may be ambiguous."))
    else:
        items.append(make_item("No data category",
                               ("info", "legend", "no_data"),
                               no_data, "unknown"))

    # EXPLICIT OTHER
    exp_other = legend_dict.get("explicit_other")
    if exp_other == "yes":
        items.append(make_item("Explicit 'Other' category",
                               ("info", "legend", "explicit_other"),
                               exp_other, "good"))
    elif exp_other == "no":
        items.append(make_item("Explicit 'Other' category",
                               ("info", "legend", "explicit_other"),
                               exp_other, "unknown",
                               "May not be needed depending on semantic type."))
    else:
        items.append(make_item("Explicit 'Other' category",
                               ("info", "legend", "explicit_other"),
                               exp_other, "unknown"))

    # INCOMPLETE INFO
    incomplete = legend_dict.get("incomplete_info")
    if incomplete == "no":
        items.append(make_item("Incomplete info",
                               ("info", "legend", "incomplete_info"),
                               incomplete, "good"))
    elif incomplete == "yes":
        items.append(make_item("Incomplete info",
                               ("info", "legend", "incomplete_info"),
                               incomplete, "bad",
                               "Legend is missing some colours/data."))
    else:
        items.append(make_item("Incomplete info",
                               ("info", "legend", "incomplete_info"),
                               incomplete, "unknown"))

    # DATA TYPE
    data_type = legend_dict.get("data_type")
    if data_type in ["nominal", "ordinal", "interval", "ratio"]:
        items.append(make_item("Data type",
                               ("info", "legend", "data_type"),
                               data_type, "good"))
    else:
        items.append(make_item("Data type",
                               ("info", "legend", "data_type"),
                               data_type, "bad",
                               "Data type not clearly identified."))

    # CONTIGUITY
    contig = legend_dict.get("contiguity")
    if contig in ["yes", "no", "not applicable"]:
        items.append(make_item("Contiguity",
                               ("info", "legend", "contiguity"),
                               contig, "unknown"))
    else:
        items.append(make_item("Contiguity",
                               ("info", "legend", "contiguity"),
                               contig, "unknown",
                               "Contiguity not clearly specified."))

    # NUMBER OF BINS
    num_bins = legend_dict.get("num_bins")
    status, detail = "unknown", ""
    if isinstance(num_bins, int):
        if 3 <= num_bins <= 7:
            status = "good"
        else:
            status = "bad"
            detail = "Too few or too many bins for clear interpretation."
    elif isinstance(num_bins, str) and num_bins.lower() == "not applicable":
        status = "unknown"
    items.append(make_item("Number of bins",
                           ("info", "legend", "num_bins"),
                           num_bins, status, detail))

    # COLOUR SCHEME
    colour_scheme = legend_dict.get("colour_scheme")
    if colour_scheme in [
        "Sequential Single-hue",
        "Sequential Multi-hue",
        "Categorical",
        "Diverging",
        "Cyclic",
        "Other",
        "Not Applicable",
    ]:
        items.append(make_item("Colour scheme",
                               ("info", "legend", "colour_scheme"),
                               colour_scheme, "good"))
    else:
        items.append(make_item("Colour scheme",
                               ("info", "legend", "colour_scheme"),
                               colour_scheme, "bad",
                               "Colour scheme not identified."))

    # COLOURS
    colours = legend_dict.get("colours")
    if colours:
        items.append(make_item("Colours",
                               ("info", "legend", "colours"),
                               colours, "unknown"))
    else:
        items.append(make_item("Colours",
                               ("info", "legend", "colours"),
                               colours, "unknown",
                               "No explicit list of legend colours."))

    # LEGEND PLACEMENT
    placement = legend_dict.get("placement")
    if placement in [
        "top left", "top center", "top right",
        "middle left", "center", "middle right",
        "bottom left", "bottom center", "bottom right",
    ]:
        if placement == "center":
            status, detail = "bad", "Legend centered may obscure map content."
        else:
            status, detail = "good", None
        items.append(make_item("Legend placement",
                               ("info", "legend", "placement"),
                               placement, status, detail))
    else:
        items.append(make_item("Legend placement",
                               ("info", "legend", "placement"),
                               placement, "unknown"))

    # BORDER FOR LEGEND
    border = legend_dict.get("border")
    if border in ["yes", "no", "not applicable"]:
        items.append(make_item("Legend border",
                               ("info", "legend", "border"),
                               border, "unknown"))
    else:
        items.append(make_item("Legend border",
                               ("info", "legend", "border"),
                               border, "unknown",
                               "Border information not clear."))

    # VARIABLES
    variables = info.get("variables")
    if isinstance(variables, int) and variables >= 1:
        if variables == 1:
            status, detail = "good", None
        else:
            status, detail = "unknown", "Multiple variables may increase complexity."
    else:
        status, detail = "bad", "Number of variables not clearly identified."
    items.append(make_item("Variables",
                           ("info", "variables"),
                           variables, status, detail))

    # FREQUENCY
    frequency = info.get("frequency")
    if frequency in ["yes", "no"]:
        items.append(make_item("Frequency shown",
                               ("info", "frequency"),
                               frequency, "unknown"))
    else:
        items.append(make_item("Frequency shown",
                               ("info", "frequency"),
                               frequency, "unknown",
                               "Frequency information not clear."))

    # SEMANTIC TYPE
    semantic = info.get("semantic_type")
    if semantic and isinstance(semantic, str) and semantic.strip():
        items.append(make_item("Semantic type",
                               ("info", "semantic_type"),
                               semantic, "good"))
    else:
        items.append(make_item("Semantic type",
                               ("info", "semantic_type"),
                               semantic, "bad",
                               "What the data represents is unclear."))

    # BACKGROUND COLOUR
    bg = info.get("bgcolour")
    if bg:
        items.append(make_item("Background colour",
                               ("info", "bgcolour"),
                               bg, "unknown"))
    else:
        items.append(make_item("Background colour",
                               ("info", "bgcolour"),
                               bg, "unknown",
                               "Background colour not identified."))

    # CLASSIFICATION
    classification = info.get("classification")
    if classification in [
        "Equal Interval", "Pretty Breaks", "Geometric", "Exponential",
        "Quantile", "Percentile", "Standard Deviation", "Maximum Breaks",
        "Unclassed", "Manual Intervals",
    ]:
        items.append(make_item("Classification method",
                               ("info", "classification"),
                               classification, "good"))
    else:
        items.append(make_item("Classification method",
                               ("info", "classification"),
                               classification, "bad",
                               "Classification method unclear."))

    return items
