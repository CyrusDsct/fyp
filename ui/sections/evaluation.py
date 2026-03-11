#evaluation.py
import streamlit as st

def render_evaluation(analysis_json: dict, item_by_label: dict | None = None):
    st.subheader("AI Evaluation")

    explanation = analysis_json.get("explanation", "unknown") if isinstance(analysis_json, dict) else "unknown"
    map_quality = analysis_json.get("map_quality", "unknown") if isinstance(analysis_json, dict) else "unknown"
    recommendations = analysis_json.get("recommendations", "none") if isinstance(analysis_json, dict) else "none"

    good = bad = neutral = 0
    if item_by_label:
        for it in item_by_label.values():
            q = (it.get("quality") or "").lower()
            if q == "good":
                good += 1
            elif q == "bad":
                bad += 1
            else:
                neutral += 1

    denom = good + bad
    score = (good / denom * 100.0) if denom > 0 else None

    if score is None:
        st.markdown(
            "<div style='color:#dc2626; font-weight:700; font-size:20px;'>"
            "Score: N/A (no good/bad criteria found)"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='color:#dc2626; font-weight:700; font-size:28px; line-height:1.1;'>"
            f"The quality of your map is {score:.1f}% !"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Factual explanation")
    st.write(explanation)

    st.markdown("#### Quality evaluation")
    st.write(map_quality)

    st.markdown("#### Recommendations")
    st.write(recommendations)
