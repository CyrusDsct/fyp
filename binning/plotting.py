import matplotlib.pyplot as plt

def plot_all(values, method_bins):
    fig, axes = plt.subplots(4, 4, figsize=(10, 8))
    axes = axes.flatten()
    for i, (method, meta) in enumerate(method_bins.items()):
        ax = axes[i]
        ax.hist(values, bins=30, color="lightgray", edgecolor="black")
        for b in meta["binBreaks"]:
            ax.axvline(b, color="red", linestyle="--", linewidth=0.8)
        ax.set_title(method, fontsize=8)
        ax.tick_params(axis="both", labelsize=6)
    for j in range(len(method_bins), len(axes)):
        axes[j].axis("off")
    plt.tight_layout()
    plt.show()
