import streamlit as st

from ui.sections.diagram import render_binning_overview


def render_evaluation(analysis_json: dict, item_by_label: dict | None = None):
    render_binning_overview(analysis_json)
