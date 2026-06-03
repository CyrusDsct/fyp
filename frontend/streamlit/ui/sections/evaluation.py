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
    def should_highlight(phrase: str) -> bool:
        normalized = re.sub(r"\s+", " ", phrase or "").strip()
        if not normalized:
            return False

        lower = normalized.lower()
        weak_terms = {
            "a",
            "an",
            "and",
            "as",
            "because",
            "but",
            "data",
            "good",
            "however",
            "legend",
            "map",
            "none",
            "or",
            "the",
            "this",
            "while",
            "with",
        }
        if lower in weak_terms:
            return False

        words = re.findall(r"[A-Za-z0-9%]+", normalized)
        has_number_or_symbol = bool(re.search(r"[\d%]", normalized))
        return len(words) >= 2 or has_number_or_symbol or len(normalized) >= 14

    pieces = []
    cursor = 0
    for match in re.finditer(r"\*\*(.+?)\*\*", str(text), flags=re.DOTALL):
        pieces.append(html.escape(str(text)[cursor:match.start()]))
        phrase = match.group(1)
        escaped_phrase = html.escape(phrase)
        if should_highlight(phrase):
            pieces.append(f'<span class="overview-highlight">{escaped_phrase}</span>')
        else:
            pieces.append(escaped_phrase)
        cursor = match.end()

    pieces.append(html.escape(str(text)[cursor:]))
    return "".join(pieces).replace("**", "").replace("\n", "<br>")


def _clean_recommendations(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return "none"

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Some model responses append a stray standalone "None" after real advice.
    if cleaned.lower() != "none":
        cleaned = re.sub(r"(?i)(?:\s*[.;])?\s*none\s*$", "", cleaned).strip()
        cleaned = cleaned.rstrip(" ;.")
        if cleaned:
            cleaned += "."

    return cleaned or "none"


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


def _render_input_context(analysis_json: dict):
    context = analysis_json.get("input_context") if isinstance(analysis_json, dict) else None
    if not isinstance(context, dict):
        return

    audience = str(context.get("audience") or "unknown").strip()
    purpose = str(context.get("purpose") or "unknown").strip()
    if audience.lower() == "unknown" and purpose.lower() == "unknown":
        return

    safe_audience = html.escape(audience or "unknown")
    safe_purpose = html.escape(purpose or "unknown")
    st.markdown(
        (
            '<div class="overview-card">'
            '<div class="overview-section-title">Analysis Context</div>'
            '<div class="overview-copy">'
            f'<span class="overview-highlight">Audience:</span> {safe_audience}<br>'
            f'<span class="overview-highlight">Purpose:</span> {safe_purpose}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_evaluation(analysis_json: dict, items: list[dict] | None = None):
    score, breakdown, _scored_total = _quality_summary(items)
    explanation = _summary_text(analysis_json, "explanation")
    map_quality = _summary_text(analysis_json, "map_quality")
    recommendations = _clean_recommendations(_summary_text(analysis_json, "recommendations", fallback="none"))
    if recommendations.strip().lower() == "none":
        recommendations = _bad_criteria_summary(items)

    st.markdown(
        (
            '<div class="overview-score-card">'
            f'<div class="overview-score-copy">The quality of your map is: <span class="overview-score-value">{score:.3g}%</span> !</div>'
            '<div class="overview-score-note-wrap">'
            f'<div class="overview-score-pill good">{breakdown["good"]} good criteria</div>'
            f'<div class="overview-score-pill">{breakdown["neutral"]} neutral criteria</div>'
            f'<div class="overview-score-pill bad">{breakdown["bad"]} bad criteria</div>'
        ),
        unsafe_allow_html=True,
    )

    _render_input_context(analysis_json)
    _render_overview_section("Explanation", explanation)
    _render_overview_section("Map Quality", map_quality)
    _render_overview_section("Recommendations", recommendations)
