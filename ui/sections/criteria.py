import html
import json
import re

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

TOPIC_RULES = [
    ("Color", ("color", "colour")),
    ("Legend", ("legend",)),
    ("Title", ("title", "subtitle")),
    ("Source", ("source", "citation")),
    ("Geography", ("region", "geographic", "projection", "administrative")),
    ("Data", ("data", "normalization", "variable", "coverage")),
    ("Map", ("map", "choropleth", "readability", "visual")),
]


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


def _format_text_for_html(value) -> str:
    text = _as_str(value, default="")
    if not text:
        return ""

    # Remove lightweight Markdown markers that should not leak into card UI.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.*?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.replace("**", "").replace("__", "")

    return html.escape(text).replace("\n", "<br>")


def _get_obj(data: dict, key: str):
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, dict) else None


def _leaf_from_path(path: str) -> str:
    base = path.split("[", 1)[0]
    return base.split(".")[-1]


def _section_for_item(path: str, quality: str) -> str:
    if (quality or "").lower().strip() == "meta":
        return "Metadata"
    return "Map-related"


def _topic_for_item(path: str, label: str, section: str) -> str:
    haystack = f"{path} {label}".lower()

    if _leaf_from_path(path) in BINNING_KEYS:
        return "Binning"

    for topic, keywords in TOPIC_RULES:
        if any(keyword in haystack for keyword in keywords):
            return topic

    if section == "Metadata":
        return "Metadata"
    return "Map"


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
                "label": label_for(item_id),
                "value": _as_str(obj.get("value")),
                "quality": _as_str(obj.get("quality"), "neutral").lower().strip(),
                "explanation": _as_str(obj.get("explanation")),
                "fixes": _as_str(obj.get("fixes"), "none"),
                "raw": obj,
            }
            item["section"] = _section_for_item(item_id, item["quality"])
            item["topic"] = _topic_for_item(item_id, item["label"], item["section"])
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

    section_order = {"Binning": 0, "Map-related": 1, "Metadata": 2}
    items.sort(key=lambda item: (section_order.get(item["section"], 9), item["label"].lower(), item["id"].lower()))
    return items, item_by_id


def _quality_chip(quality: str) -> str:
    quality = (quality or "neutral").lower().strip()
    if quality == "good":
        return '<span class="criterion-chip good">GOOD</span>'
    if quality == "bad":
        return '<span class="criterion-chip bad">BAD</span>'
    if quality == "meta":
        return '<span class="criterion-chip meta">META</span>'
    return '<span class="criterion-chip neutral">NEUTRAL</span>'


def _topic_chip(topic: str) -> str:
    return f'<span class="criterion-topic-chip">{_format_text_for_html(topic)}</span>'


def _render_filters(items: list, filter_key: str):
    show_status_filter = filter_key == "map_related"
    qualities = ["good", "neutral", "bad"] if show_status_filter else []

    topics = sorted({item.get("topic", "Other") for item in items})
    quality_key = f"{filter_key}_qualities"
    topic_key = f"{filter_key}_topics"

    if show_status_filter:
        current_qualities = st.session_state.get(quality_key)
        if not isinstance(current_qualities, list) or any(value not in qualities for value in current_qualities):
            st.session_state[quality_key] = qualities.copy()

    current_topics = st.session_state.get(topic_key)
    if not isinstance(current_topics, list) or any(value not in topics for value in current_topics):
        st.session_state[topic_key] = topics.copy()

    if show_status_filter:
        col1, col2 = st.columns(2, gap="small")
        with col1:
            selected_qualities = st.multiselect(
                "Status",
                options=qualities,
                key=quality_key,
                placeholder="Choose status",
            )
        with col2:
            selected_topics = st.multiselect(
                "Topic",
                options=topics,
                key=topic_key,
                placeholder="Choose topic",
            )
    else:
        selected_topics = st.multiselect(
            "Topic",
            options=topics,
            key=topic_key,
            placeholder="Choose topic",
        )
        selected_qualities = None

    return selected_qualities, selected_topics


def render_item_cards(items: list, empty_text: str, filter_key: str | None = None, section_name: str | None = None):
    if not items:
        st.caption(empty_text)
        return

    filtered_items = items
    if filter_key:
        selected_qualities, selected_topics = _render_filters(items, filter_key)
        filtered_items = [
            item
            for item in items
            if (selected_qualities is None or item.get("quality") in selected_qualities)
            and item.get("topic") in selected_topics
        ]

        if not filtered_items:
            if filter_key == "map_related" and selected_qualities and "bad" in selected_qualities:
                bad_count = sum(1 for item in items if item.get("quality") == "bad")
                if bad_count == 0:
                    st.caption("No bad items exist in Map-related for this analysis. Any score reduction is likely coming from Binning.")
                    return
            st.caption("No items match the current filters.")
            return

    for item in filtered_items:
        value_html = _format_text_for_html(item.get("value", ""))
        explanation_html = _format_text_for_html(item.get("explanation", ""))
        fixes = item.get("fixes", "none")
        fixes_html = _format_text_for_html(fixes)
        label_html = _format_text_for_html(item.get("label", "Unknown"))
        fixes_block = ""
        if fixes and str(fixes).strip().lower() != "none":
            fixes_block = (
                '<div class="criterion-row">'
                '<div class="criterion-key">Fixes</div>'
                f'<div class="criterion-body">{fixes_html}</div>'
                "</div>"
            )

        head_left = (
            '<div class="criterion-head-left">'
            f'<div class="criterion-title">{label_html}</div>'
            f'{_topic_chip(item.get("topic", "Other"))}'
            "</div>"
        )

        st.markdown(
            (
                '<div class="criterion-card">'
                '<div class="criterion-head">'
                f"{head_left}"
                f'<div class="criterion-chip-wrap">{_quality_chip(item.get("quality", "neutral"))}</div>'
                "</div>"
                '<div class="criterion-row">'
                '<div class="criterion-key">Value</div>'
                f'<div class="criterion-body">{value_html}</div>'
                "</div>"
                '<div class="criterion-row">'
                '<div class="criterion-key">Explanation</div>'
                f'<div class="criterion-body">{explanation_html}</div>'
                "</div>"
                f"{fixes_block}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def render_details_panel(analysis_json: dict, items: list):
    if not items:
        st.info("No detail items were found in the analysis JSON.")
        st.json(analysis_json)
        return

    binning_items = [item for item in items if item.get("section") == "Binning"]
    map_items = [item for item in items if item.get("section") == "Map-related"]
    metadata_items = [item for item in items if item.get("section") == "Metadata"]

    binning_tab, map_tab, metadata_tab = st.tabs(["Binning", "Map-related", "Metadata"])

    with map_tab:
        render_item_cards(map_items, "No map-related details were found.", filter_key="map_related", section_name="Map-related")

    with metadata_tab:
        render_item_cards(metadata_items, "No metadata details were found.", filter_key="metadata", section_name="Metadata")

    return binning_tab, binning_items
