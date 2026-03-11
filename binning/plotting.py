import numpy as np
import streamlit as st
import matplotlib.pyplot as plt


def draw_interval_bar(
    edges,
    title,
    subtitle=None,
    cmap_name="viridis",
    data=None,
    use_frequency_height=False,
):
    edges = np.array(edges, dtype=float)
    edges = edges[np.isfinite(edges)]

    if edges.size < 2:
        st.warning(f"{title}: not enough valid edges to draw intervals.")
        return

    edges = np.unique(np.sort(edges))
    if edges.size < 2:
        st.warning(f"{title}: not enough distinct edges to draw intervals.")
        return

    minv, maxv = float(edges[0]), float(edges[-1])
    if (not np.isfinite(minv)) or (not np.isfinite(maxv)) or (minv == maxv):
        st.warning(f"{title}: invalid axis limits (min={minv}, max={maxv}).")
        return

    counts = None
    max_count = None
    if use_frequency_height and (data is not None):
        data_arr = np.array(data, dtype=float)
        data_arr = data_arr[np.isfinite(data_arr)]
        if data_arr.size > 0:
            counts, _ = np.histogram(data_arr, bins=edges)
            max_count = int(counts.max()) if counts.size > 0 else 0
            if max_count <= 0:
                use_frequency_height = False
        else:
            use_frequency_height = False

    # ---- Make the chart compact (key for "no scrolling") ----
    fig, ax = plt.subplots(figsize=(6, 0.55))  #  much shorter than before

    width_total = maxv - minv
    ax.barh(
        y=0,
        width=width_total,
        left=minv,
        height=0.22,         
        color="red",
        edgecolor="none",
        alpha=0.30,
    )

    cmap = plt.get_cmap(cmap_name)
    n_int = len(edges) - 1

    for i in range(n_int):
        left = float(edges[i])
        right = float(edges[i + 1])
        if (not np.isfinite(left)) or (not np.isfinite(right)) or (right <= left):
            continue

        # optional height by frequency (usually makes things taller,default False)
        if use_frequency_height and (counts is not None) and (max_count is not None) and max_count > 0:
            h = 0.16 + 0.24 * (counts[i] / max_count) 
        else:
            h = 0.32  # thin bar

        c = cmap((i + 0.5) / max(n_int, 1))
        ax.barh(
            y=0,
            width=right - left,
            left=left,
            height=h,
            color=c,
            edgecolor="white",
            linewidth=0.6,
        )

    # axes styling (compact)
    ax.set_yticks([])
    ax.set_xlim(minv, maxv)
    ax.set_ylim(-0.45, 0.45) 
    ax.set_xticks(edges)
    ax.set_xticklabels([f"{e:.2f}" for e in edges], rotation=0, fontsize=7)

    full_title = title if subtitle is None else f"{title} ({subtitle})"
    ax.set_title(full_title, fontsize=9, pad=2)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    fig.tight_layout(pad=0.2)

    st.pyplot(fig, clear_figure=True)
    plt.close(fig)