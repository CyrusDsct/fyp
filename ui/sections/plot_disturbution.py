import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def plot_distribution(series: pd.Series):
    s = series.dropna()
    if s.empty:
        st.info("No data to plot (all values are empty).")
        return

    if pd.api.types.is_numeric_dtype(s):
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.hist(s.astype(float), bins=20, color="#2563eb", edgecolor="white")
        ax.set_title("Distribution")
        ax.set_xlabel("Value")
        ax.set_ylabel("Count")
        st.pyplot(fig, clear_figure=True, use_container_width=True)
    else:
        vc = s.astype(str).value_counts().head(20)
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.barh(list(reversed(vc.index)), list(reversed(vc.values)), color="#2563eb")
        ax.set_title("Distribution (Top categories)")
        ax.set_xlabel("Count")
        st.pyplot(fig, clear_figure=True, use_container_width=True)