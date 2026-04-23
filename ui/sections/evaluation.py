import streamlit as st
import html
import re


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


def _quality_score(items: list[dict] | None) -> float:
    items = items or []
    good = sum(1 for item in items if item.get("quality") == "good")
    bad = sum(1 for item in items if item.get("quality") == "bad")
    denominator = good + bad
    if denominator == 0:
        return 0.0
    return good / denominator * 100


def _section_quality_breakdown(items: list[dict] | None) -> dict[str, dict[str, int]]:
    breakdown = {
        "Map-related": {"good": 0, "bad": 0},
        "Metadata": {"good": 0, "bad": 0},
    }
    for item in items or []:
        section = item.get("section")
        quality = item.get("quality")
        if section in breakdown and quality in {"good", "bad"}:
            breakdown[section][quality] += 1
    return breakdown


def _bad_criteria_summary(items: list[dict] | None) -> str:
    items = items or []
    bad_items = [item for item in items if item.get("quality") == "bad"]
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
    score = _quality_score(items)
    breakdown = _section_quality_breakdown(items)
    explanation = _summary_text(analysis_json, "explanation")
    map_quality = _summary_text(analysis_json, "map_quality")
    recommendations = _summary_text(analysis_json, "recommendations", fallback="none")
    if recommendations.strip().lower() == "none":
        recommendations = _bad_criteria_summary(items)

    st.markdown(
        (
            '<div class="overview-score-card">'
            f'<div class="overview-score-copy">The quality of your map is <span class="overview-score-value">{score:.3g}%</span>!</div>'
            '<div class="overview-score-note-wrap">'
            f'<div class="overview-score-pill good">{breakdown["Map-related"]["good"]} good criterias</div>'
            f'<div class="overview-score-pill bad">{breakdown["Map-related"]["bad"]} bad criterias</div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    _render_overview_section("Explanation", explanation)
    _render_overview_section("Map Quality", map_quality)
    _render_overview_section("Recommendations", recommendations)
