import json

import streamlit as st


BINNING_KEYS = {
    "number_of_bins",
    "data_breaks",
    "data_contiguity",
    "classification_method",
    "data_distribution",
    "bin_count_appropriateness",
    "data_breaks_quality",
    "classification_appropriateness",
}


def _as_str(value, default="unknown"):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)

    text = str(value).strip()
    return text if text else default


def _get_obj(data: dict, key: str):
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, dict) else None


def _leaf_from_path(path: str) -> str:
    base = path.split("[", 1)[0]
    return base.split(".")[-1]


def _section_for_item(path: str) -> str:
    base = path.split("[", 1)[0]
    leaf = _leaf_from_path(path)

    if leaf in BINNING_KEYS:
        return "Binning related"

    if base.startswith("facts.metadata."):
        return "Other"

    return "Map related"


def build_criteria_items(analysis_json: dict):
    extract = _get_obj(analysis_json, "extract") or {}

    if not extract:
        skip = {"explanation", "map_quality", "recommendations", "status", "analysis", "binning_similarity"}
        extract = {}
        for key, value in (analysis_json or {}).items():
            if key not in skip:
                extract[key] = value

    leaf_labels = {
        "number_of_bins": "Number of bins",
        "data_breaks": "Data breaks",
        "data_contiguity": "Data contiguity",
        "number_of_variables": "Number of variables",
        "region_count": "Region count",
        "coverage_percentage": "Coverage percentage",
        "color_scheme": "Colour scheme",
        "legend_colors": "Legend colours",
        "legend_presence": "Legend present",
        "legend_orientation": "Legend orientation",
        "legend_placement": "Legend placement",
        "frequency_labels": "Frequency labels",
        "title_presence": "Title present",
        "title_text": "Title text",
        "subtitle_presence": "Subtitle present",
        "subtitle_text": "Subtitle text",
        "map_projection": "Map projection",
        "background_color": "Background colour",
        "source_citation": "Source citation",
        "data_distribution": "Data distribution",
        "classification_method": "Classification method",
        "normalization_present": "Normalization present",
        "normalization_type": "Normalization type",
        "geographic_unit_homogeneous": "Geographic unit homogeneous",
        "geographic_unit_homogenous": "Geographic unit homogeneous",
        "administrative_level": "Administrative level",
        "legend_completeness": "Legend completeness",
        "handling_no_missing_data": "Missing-data handling",
        "source_recency": "Source recency",
        "bin_count_appropriateness": "Bin count appropriateness",
        "data_breaks_quality": "Data breaks quality",
        "classification_appropriateness": "Classification appropriateness",
        "choropleth_suitability": "Choropleth suitability",
        "region_hierarchy_consistency": "Region hierarchy consistency",
        "data_coverage_adequacy": "Data coverage adequacy",
        "color_scheme_appropriateness": "Colour scheme appropriateness",
        "color_distinguishability": "Colour distinguishability",
        "legend_placement_quality": "Legend placement quality",
        "title_quality": "Title quality",
        "subtitle_quality": "Subtitle quality",
        "information_readability": "Information readability",
        "information_specificity": "Information specificity",
        "visual_readability": "Visual readability",
        "source_quality": "Source quality",
    }

    def is_item_dict(data):
        return isinstance(data, dict) and any(key in data for key in ("value", "quality", "explanation", "fixes"))

    def to_title_from_key(key: str) -> str:
        label = (key or "").replace("_", " ").strip()
        return label[:1].upper() + label[1:] if label else "Unknown"

    def label_for(path: str) -> str:
        leaf = _leaf_from_path(path)
        if leaf in leaf_labels:
            return leaf_labels[leaf]
        return to_title_from_key(leaf)

    items = []
    item_by_id = {}

    def walk(obj, path=""):
        if is_item_dict(obj):
            item_id = path or "unknown"
            item = {
                "id": item_id,
                "section": _section_for_item(item_id),
                "label": label_for(item_id),
                "value": _as_str(obj.get("value")),
                "quality": _as_str(obj.get("quality"), "neutral").lower().strip(),
                "explanation": _as_str(obj.get("explanation")),
                "fixes": _as_str(obj.get("fixes"), "none"),
                "raw": obj,
            }
            items.append(item)
            item_by_id[item_id] = item
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else str(key)
                walk(value, new_path)
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                new_path = f"{path}[{index}]"
                walk(value, new_path)

    walk(extract, "")

    section_order = {"Binning related": 0, "Map related": 1, "Other": 2}
    items.sort(key=lambda item: (section_order.get(item["section"], 9), item["label"].lower(), item["id"].lower()))
    return items, item_by_id


def _render_item_list(items: list, empty_text: str):
    if not items:
        st.caption(empty_text)
        return

    icon_map = {
        "good": "[GOOD]",
        "bad": "[BAD]",
        "neutral": "[NEUTRAL]",
        "meta": "[META]",
    }

    for item in items:
        quality = (item.get("quality") or "neutral").lower().strip()
        icon = icon_map.get(quality, "[NEUTRAL]")
        title = f"{icon} {item.get('label', 'Unknown')} [{quality.upper()}]"

        with st.expander(title, expanded=False):
            st.markdown(f"**Value:** {item.get('value', '')}")
            st.markdown(f"**Explanation:** {item.get('explanation', '')}")
            fixes = item.get("fixes", "none")
            if fixes and str(fixes).strip().lower() != "none":
                st.markdown(f"**Fixes:** {fixes}")


def render_details(analysis_json: dict, items: list):
    st.subheader("Details")

    if not items:
        st.info("No detail items were found in the analysis JSON.")
        st.json(analysis_json)
        return

    binning_items = [item for item in items if item.get("section") == "Binning related"]
    map_items = [item for item in items if item.get("section") == "Map related"]
    other_items = [item for item in items if item.get("section") == "Other"]

    st.markdown("#### Binning related")
    _render_item_list(binning_items, "No binning-related details were found.")

    st.markdown("#### Map related")
    _render_item_list(map_items, "No map-related details were found.")

    st.markdown("#### Other")
    _render_item_list(other_items, "No metadata details were found.")


def render_criteria(analysis_json: dict, items: list):
    render_details(analysis_json, items)
