import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Assign value in data to bin
def bin_metadata(raw_data, bin_edges):
    bin_edges = np.unique(np.sort(bin_edges))
    bin_assignments = np.digitize(raw_data, bin_edges, right=False) - 1
    i = 0
    while i < len(bin_assignments):
        if bin_assignments[i] == len(bin_edges) - 1:
            bin_assignments[i] = len(bin_edges) - 2
        i += 1

    s = pd.Series(bin_assignments)
    bin_sizes_series = s.value_counts().sort_index()
    # Convert to dict with integer keys
    bin_sizes = {}
    for idx in bin_sizes_series.index:
        bin_sizes[int(idx)] = int(bin_sizes_series.loc[idx])

    bin_breaks = []
    k = 0
    while k < len(bin_edges):
        bin_breaks.append(float(bin_edges[k]))
        k += 1

    return {
        "rawData": raw_data,
        "dataRange": [float(raw_data.min()), float(raw_data.max())],
        "binCount": len(bin_edges) - 1,
        "binBreaks": bin_breaks,
        "binSizes": bin_sizes,
        "dataBinAssignments": bin_assignments.tolist()
    }


# All Binning Algorithms
def equal_interval(data, bins):
    minv = data.min()
    maxv = data.max()
    interval = (maxv - minv) / bins
    edges = []
    i = 0
    while i < (bins + 1):
        edge = minv + i * interval
        edges.append(edge)
        i += 1
    return np.array(edges)


def defined_interval(data, interval):
    minv = data.min()
    maxv = data.max()
    edges = [minv]
    while edges[-1] < maxv:
        next_edge = edges[-1] + interval
        if next_edge >= maxv:
            edges.append(maxv)
            break
        edges.append(next_edge)
    return np.array(edges)


def exponential_bins(data, bins):
    N = len(data)
    powers = []
    i = 0
    while i < bins:
        powers.append(2 ** i)
        i += 1
    powers = np.array(powers)

    sizes = powers / powers.sum() * N
    sizes = np.round(sizes).astype(int)
    if len(sizes) > 1:
        sizes[-1] = int(N - sizes[:-1].sum())
    else:
        sizes[-1] = int(N)

    sorted_data = np.sort(data)
    breaks = [sorted_data[0]]
    idx = 0
    j = 0
    while j < (len(sizes) - 1):
        idx += int(sizes[j])
        if idx < 0:
            idx = 0
        if idx > N - 1:
            idx = N - 1
        breaks.append(sorted_data[idx])
        j += 1
    breaks.append(sorted_data[-1])
    uniq = []
    p = 0
    while p < len(breaks):
        val = breaks[p]
        if val not in uniq:
            uniq.append(val)
        p += 1
    return np.array(uniq)


def geometric_interval(data, bins):
    minv = data.min()
    maxv = data.max()
    if minv <= 0:
        positive = data[data > 0]
        if len(positive) > 0:
            minv = float(np.min(positive))
        else:
            minv = 1e-9
    ratio = (maxv / minv) ** (1.0 / bins)
    edges = [minv]
    i = 1
    while i < bins:
        edges.append(minv * (ratio ** i))
        i += 1
    edges.append(maxv)
    return np.array(edges)


def maxbreaks_bins(data, bins):
    arr = np.sort(data)
    diffs = arr[1:] - arr[:-1]
    if len(diffs) < bins - 1:
        edges = [arr[0], arr[-1]]
    else:
        idxs = np.argsort(diffs)
        selected = idxs[-(bins - 1):]
        selected_sorted = np.sort(selected)
        edges = [arr[0]]
        m = 0
        while m < len(selected_sorted):
            edges.append(arr[selected_sorted[m] + 1])
            m += 1
        edges.append(arr[-1])

    uniq = []
    t = 0
    while t < len(edges):
        v = edges[t]
        if v not in uniq:
            uniq.append(v)
        t += 1
    return np.array(uniq)


def quantile_bins(data, bins):
    edges = []
    qs = np.linspace(0, 1, bins + 1)
    i = 0
    while i < len(qs):
        q = qs[i]
        edges.append(np.quantile(data, q))
        i += 1
    return np.array(edges)


def boxplot_bins(data):
    q1 = np.percentile(data, 25)
    q2 = np.percentile(data, 50)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    edges = [data.min(), lower, q1, q2, q3, upper, data.max()]
    uniq = []
    i = 0
    while i < len(edges):
        if edges[i] not in uniq:
            uniq.append(edges[i])
        i += 1
    return np.array(uniq)


def stdev_bins(data, bins, mean_as_boundary=True, sdfactor=1.0):
    mu = np.mean(data)
    sigma = np.std(data)
    edges = []
    if mean_as_boundary:
        i = 0
        while i < (bins + 1):
            edges.append(mu + (i - bins // 2) * sdfactor * sigma)
            i += 1
    else:
        if bins % 2 == 0:
            raise ValueError('Variant 2 only works for odd bin count.')
        mid = bins // 2
        i = 0
        while i < (bins + 1):
            edges.append(mu + (i - mid - 0.5) * sdfactor * sigma)
            i += 1
    new_edges = []
    new_edges.append(data.min())
    p = 0
    while p < len(edges):
        new_edges.append(edges[p])
        p += 1
    new_edges.append(data.max())
    # unique
    uniq = []
    r = 0
    while r < len(new_edges):
        if new_edges[r] not in uniq:
            uniq.append(new_edges[r])
        r += 1
    return np.array(uniq)


def headtail_bins(data):
    breaks = []
    x = np.sort(data)
    while len(x) > 1:
        mean_val = np.mean(x)
        breaks.append(mean_val)
        x = x[x > mean_val]
        if len(breaks) > 20:
            break
    edges = [data.min()]
    sorted_breaks = sorted(breaks)
    s = 0
    while s < len(sorted_breaks):
        edges.append(sorted_breaks[s])
        s += 1
    edges.append(data.max())
    # unique
    uniq = []
    u = 0
    while u < len(edges):
        if edges[u] not in uniq:
            uniq.append(edges[u])
        u += 1
    return np.array(uniq)


def pretty_bins(data, bins):
    minv = float(np.min(data))
    maxv = float(np.max(data))
    step = (maxv - minv) / bins
    mag = 10 ** np.floor(np.log10(step))
    nice_step = np.ceil(step / mag) * mag
    nice_min = np.floor(minv / mag) * mag
    nice_max = np.ceil(maxv / mag) * mag
    edges = []
    i = 0
    while i < (bins + 1):
        edges.append(nice_min + i * nice_step)
        i += 1
    if edges[-1] < nice_max:
        edges.append(nice_max)
    uniq = []
    t = 0
    while t < len(edges):
        if edges[t] not in uniq:
            uniq.append(edges[t])
        t += 1
    return np.array(uniq)


# 1D similarity algorithm
def bin_similarity_1d(manual_ranges, auto_ranges):
    overlap = 0.0
    i = 0
    while i < len(manual_ranges):
        m = manual_ranges[i]
        j = 0
        while j < len(auto_ranges):
            a = auto_ranges[j]
            start = max(m[0], a[0])
            end = min(m[1], a[1])
            if end - start > 0:
                overlap += (end - start)
            j += 1
        i += 1

    manual_total = 0.0
    i = 0
    while i < len(manual_ranges):
        m = manual_ranges[i]
        manual_total += (m[1] - m[0])
        i += 1

    if manual_total > 0:
        return (overlap / manual_total) * 100.0
    else:
        return 0.0


# 2D similarity algorithm
def bin_similarity_2d(manual_meta, auto_meta):
    manual_edges = manual_meta["binBreaks"]
    auto_edges = auto_meta["binBreaks"]

    manual_ranges = []
    i = 0
    while i < (len(manual_edges) - 1):
        manual_ranges.append([manual_edges[i], manual_edges[i + 1]])
        i += 1

    auto_ranges = []
    j = 0
    while j < (len(auto_edges) - 1):
        auto_ranges.append([auto_edges[j], auto_edges[j + 1]])
        j += 1

    manual_sizes_map = manual_meta["binSizes"]
    auto_sizes_map = auto_meta["binSizes"]

    manual_sizes = []
    k = 0
    while k < len(manual_ranges):
        if k in manual_sizes_map:
            manual_sizes.append(manual_sizes_map[k])
        else:
            manual_sizes.append(0)
        k += 1

    auto_sizes = []
    k = 0
    while k < len(auto_ranges):
        if k in auto_sizes_map:
            auto_sizes.append(auto_sizes_map[k])
        else:
            auto_sizes.append(0)
        k += 1

    total_similarity = 0.0
    n = len(manual_ranges)
    k = 0
    while k < n:
        if k >= len(manual_sizes):
            break

        m_start = manual_ranges[k][0]
        m_end = manual_ranges[k][1]
        m_width = m_end - m_start
        if m_width <= 0:
            k += 1
            continue

        m_density = 0.0
        if m_width > 0:
            m_density = float(manual_sizes[k]) / float(m_width)

        overlap_area = 0.0
        manual_area = m_density * m_width

        j = 0
        while j < len(auto_ranges):
            if j >= len(auto_sizes):
                break

            a_start = auto_ranges[j][0]
            a_end = auto_ranges[j][1]
            a_width = a_end - a_start
            if a_width <= 0:
                j += 1
                continue

            a_density = float(auto_sizes[j]) / float(a_width)

            overlap_start = m_start
            if a_start > overlap_start:
                overlap_start = a_start

            overlap_end = m_end
            if a_end < overlap_end:
                overlap_end = a_end

            overlap_width = overlap_end - overlap_start
            if overlap_width > 0:
                overlap_height = m_density
                if a_density < overlap_height:
                    overlap_height = a_density
                overlap_area += overlap_width * overlap_height

            j += 1

        bin_similarity = 0.0
        if manual_area > 0:
            bin_similarity = (overlap_area / manual_area) * 100.0
        total_similarity += bin_similarity
        k += 1

    if n > 0:
        return total_similarity / float(n)
    else:
        return 0.0


# Input
filename = input("Input the name of the csv file (without folder or .csv):\n")
filename = "csv/" + filename + ".csv"
dataset = pd.read_csv(filename)
print(dataset.to_string())

value_col = input("Please enter the column number containing the data that you would like to bin by. (First column = 1)")
while not value_col.isdigit():
    value_col = input("Please enter an integer number of bins.")
value_col = dataset.columns[int(value_col) - 1]
print("You are binning by " + str(value_col))
values = dataset[value_col].values

num_bins = input("How many bins/classes? ")
while not num_bins.isdigit():
    num_bins = input("Please enter an integer number of bins. ")
num_bins = int(num_bins)

print("Input each bin's min and max")
manual_bins = np.empty((num_bins, 2))
i = 0
while i < num_bins:
    while True:
        try:
            start = float(input("Bin #{} min: ".format(i + 1)))
            break
        except ValueError:
            print("Please enter a numeric value.")
    manual_bins[i, 0] = start
    while True:
        try:
            end = float(input("Bin #{} max: ".format(i + 1)))
            break
        except ValueError:
            print("Please enter a numeric value.")
    manual_bins[i, 1] = end
    i += 1

manual_edges = list(sorted(set(manual_bins.flatten())))
method_bins = {}
method_bins["Manual"] = bin_metadata(values, manual_edges)

# Start Binning
print("\nRunning all binning methods...\n")
method_bins["Equal Interval"] = bin_metadata(values, equal_interval(values, num_bins))
method_bins["Exponential"] = bin_metadata(values, exponential_bins(values, num_bins))
method_bins["Geometric Interval"] = bin_metadata(values, geometric_interval(values, num_bins))
method_bins["Maximum Breaks"] = bin_metadata(values, maxbreaks_bins(values, num_bins))
method_bins["Quantile"] = bin_metadata(values, quantile_bins(values, num_bins))
method_bins["Box Plot"] = bin_metadata(values, boxplot_bins(values))
method_bins["Standard Deviation 1"] = bin_metadata(values, stdev_bins(values, num_bins, True, 1.0))
if num_bins % 2 == 1:
    method_bins["Standard Deviation 2"] = bin_metadata(values, stdev_bins(values, num_bins, False, 1.0))
method_bins["Pretty Breaks"] = bin_metadata(values, pretty_bins(values, num_bins))

# SImilarity Output
print("\n--- 1D Similarity to Manual Bins ---")
manual_ranges = manual_bins
similarity = []
for method, meta in method_bins.items():
    auto_ranges = []
    i = 0
    while i < (len(meta["binBreaks"]) - 1):
        auto_ranges.append([meta["binBreaks"][i], meta["binBreaks"][i + 1]])
        i += 1
    sim = bin_similarity_1d(manual_ranges, auto_ranges)
    similarity.append([method, sim])

def get_score(item):
    return item[1]

# Simple Sort
m = 0
while m < len(similarity):
    n_idx = 0
    while n_idx < len(similarity) - 1:
        if get_score(similarity[n_idx]) < get_score(similarity[n_idx + 1]):
            tmp = similarity[n_idx]
            similarity[n_idx] = similarity[n_idx + 1]
            similarity[n_idx + 1] = tmp
        n_idx += 1
    m += 1

p = 0
while p < len(similarity):
    print(str(similarity[p][0]) + ": " + "{:.2f}%".format(similarity[p][1]))
    p += 1

print("\n--- 2D Similarity to Manual Bins ---")
similarity_2d = []
for method, meta in method_bins.items():
    sim2d = bin_similarity_2d(method_bins["Manual"], meta)
    similarity_2d.append([method, sim2d])

# Sorting:)
m = 0
while m < len(similarity_2d):
    n_idx = 0
    while n_idx < len(similarity_2d) - 1:
        if similarity_2d[n_idx][1] < similarity_2d[n_idx + 1][1]:
            tmp = similarity_2d[n_idx]
            similarity_2d[n_idx] = similarity_2d[n_idx + 1]
            similarity_2d[n_idx + 1] = tmp
        n_idx += 1
    m += 1

q = 0
while q < len(similarity_2d):
    print(str(similarity_2d[q][0]) + ": " + "{:.2f}%".format(similarity_2d[q][1]))
    q += 1

r = 0
for method, meta in method_bins.items():
    print("\n=== " + str(method) + " ===")
    for key, val in meta.items():
        if key in ["rawData", "dataBinAssignments"]:
            continue
        print(str(key) + ": " + str(val))
    r += 1

# Graph Output
fig, axes = plt.subplots(4, 4, figsize=(10, 8))
axes = axes.flatten()

i = 0
for method, meta in method_bins.items():
    ax = axes[i]
    ax.hist(values, bins=30, color="lightgray", edgecolor="black")
    j = 0
    while j < len(meta["binBreaks"]):
        b = meta["binBreaks"][j]
        ax.axvline(b, color="red", linestyle="--", linewidth=0.8)
        j += 1
    ax.set_title(method, fontsize=8)
    ax.tick_params(axis="both", labelsize=6)
    i += 1

j = i
while j < len(axes):
    axes[j].axis("off")
    j += 1

plt.tight_layout()
plt.show()