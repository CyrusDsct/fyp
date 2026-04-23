import streamlit as st
import html
import re

from ui.sections import criteria as criteria_section


def _summary_text(analysis_json: dict, key: str, fallback: str = "Not available.") -> str:
    value = analysis_json.get(key) if isinstance(analysis_json, dict) else None
    if value is None:
        return fallback

    text = str(value).strip()
    if not text or text.lower() == "unknown":
        return fallback
    return text


def _render_highlight_markup(text: str) -> str:
    safe_text = html.escape(text)
    safe_text = re.sub(r"\*\*(.+?)\*\*", r'<span class="overview-highlight">\1</span>', safe_text)
    return safe_text.replace("\n", "<br>")


def _quality_summary(items: list[dict] | None) -> tuple[float, dict[str, int], int]:
    map_related_statuses = {}
    for item in items or []:
        key = criteria_section.canonical_map_related_key(str(item.get("id") or ""))
        if key is None or key in map_related_statuses:
            continue
        quality = str(item.get("quality") or "neutral").lower().strip()
        map_related_statuses[key] = quality if quality in {"good", "neutral", "bad"} else "neutral"

    breakdown = {"good": 0, "neutral": 0, "bad": 0}
    for key, _label in criteria_section.MAP_RELATED_CRITERIA:
        breakdown[map_related_statuses.get(key, "neutral")] += 1

    total = sum(breakdown.values())
    if total == 0:
        return 0.0, breakdown, total

    weighted_score = breakdown["good"] + 0.5 * breakdown["neutral"]
    return weighted_score / total * 100, breakdown, total


def _bad_criteria_summary(items: list[dict] | None) -> str:
    items = items or []
    bad_items = []
    seen = set()
    for item in items:
        key = criteria_section.canonical_map_related_key(str(item.get("id") or ""))
        if key is None or key in seen:
            continue
        if item.get("quality") == "bad":
            bad_items.append(item)
            seen.add(key)
    if not bad_items:
        return "none"

    labels = [item.get("label", "Unknown") for item in bad_items[:5]]
    return "No explicit recommendations were returned. Current **bad criteria** include " + ", ".join(labels) + "."


def _render_overview_section(title: str, body: str):
    safe_body = _render_highlight_markup(body)
    st.markdown(
        (
            '<div class="overview-card">'
            f'<div class="overview-section-title">{title}</div>'
            f'<div class="overview-copy">{safe_body}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_evaluation(analysis_json: dict, items: list[dict] | None = None):
    score, breakdown, _scored_total = _quality_summary(items)
    explanation = _summary_text(analysis_json, "explanation")
    map_quality = _summary_text(analysis_json, "map_quality")
    recommendations = _summary_text(analysis_json, "recommendations", fallback="none")
    if recommendations.strip().lower() == "none":
        recommendations = _bad_criteria_summary(items)

    # score_note = "Neutral criteria count as partial credit."

    st.markdown(
        (
            '<div class="overview-score-card">'
            f'<div class="overview-score-copy">The quality of your map is: <span class="overview-score-value">{score:.3g}%</span> !</div>'
            '<div class="overview-score-note-wrap">'
            f'<div class="overview-score-pill good">{breakdown["good"]} good criteria</div>'
            f'<div class="overview-score-pill">{breakdown["neutral"]} neutral criteria</div>'
            f'<div class="overview-score-pill bad">{breakdown["bad"]} bad criteria</div>'
            # "</div>"
            # f'<div class="overview-copy">{score_note}</div>'
            # "</div>"
        ),
        unsafe_allow_html=True,
    )

    _render_overview_section("Explanation", explanation)
    _render_overview_section("Map Quality", map_quality)
    _render_overview_section("Recommendations", recommendations)
