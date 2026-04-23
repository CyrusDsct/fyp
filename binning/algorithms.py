import warnings

import numpy as np

try:
    import mapclassify
except ImportError:
    mapclassify = None


def _clean_numeric_data(data):
    arr = np.asarray(data, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("No finite numeric data available.")
    return arr


def _unique_sorted_edges(edges):
    arr = np.asarray(edges, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return arr
    return np.unique(np.sort(arr))


def _require_mapclassify():
    if mapclassify is None:
        raise ImportError("mapclassify is required for this binning method. Install requirements.txt.")
    return mapclassify


def _run_with_known_binning_warning_suppressed(factory):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Not enough unique values in array to form .* classes\. Setting k to .*",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"Insufficient number of unique diffs\. Breaks are random\.",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"Numba not installed\. Using slow pure python version\.",
            category=UserWarning,
        )
        return factory()


def _edges_from_mapclassify(data, classifier):
    data = _clean_numeric_data(data)
    upper_bounds = np.asarray(classifier.bins, dtype=float).reshape(-1)
    edges = [float(np.min(data))]
    edges.extend([float(x) for x in upper_bounds if np.isfinite(x)])
    maxv = float(np.max(data))
    if edges[-1] < maxv:
        edges.append(maxv)
    return _unique_sorted_edges(edges)


def _nice_interval(raw_interval):
    if raw_interval <= 0 or not np.isfinite(raw_interval):
        return raw_interval
    mag = 10 ** np.floor(np.log10(raw_interval))
    scaled = raw_interval / mag
    if scaled <= 1:
        nice = 1
    elif scaled <= 2:
        nice = 2
    elif scaled <= 5:
        nice = 5
    else:
        nice = 10
    return nice * mag


def _digitize_assignments(data, edges):
    edges = _unique_sorted_edges(edges)
    if edges.size < 2:
        return None
    bins = edges.size - 1
    assignments = np.digitize(data, edges[1:-1], right=True)
    return np.clip(assignments, 0, bins - 1)


def mc_equal_interval(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.EqualInterval(data, k=int(bins))))


def mc_quantile_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.Quantiles(data, k=int(bins))))


def mc_percentile_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.Percentiles(data)))


def mc_pretty_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.PrettyBreaks(data, k=int(bins))))


def mc_boxplot_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.BoxPlot(data)))


def mc_stdev_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.StdMean(data)))


def mc_maxbreaks_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.MaximumBreaks(data, k=int(bins))))


def mc_natural_breaks(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.NaturalBreaks(data, k=int(bins))))


def mc_ckmeans_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.FisherJenks(data, k=int(bins))))


def mc_headtail_bins(data, bins):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.HeadTailBreaks(data)))


def mc_defined_interval(data, bins, interval=None):
    mc = _require_mapclassify()
    data = _clean_numeric_data(data)
    minv = float(np.min(data))
    maxv = float(np.max(data))
    if minv == maxv:
        return np.array([minv, maxv])

    if interval is None or interval <= 0 or not np.isfinite(interval):
        interval = _nice_interval((maxv - minv) / max(int(bins), 1))

    upper_bounds = []
    current = minv + interval
    guard = 0
    while current < maxv and guard < 1000:
        upper_bounds.append(float(current))
        current += interval
        guard += 1
    upper_bounds.append(maxv)
    return _edges_from_mapclassify(data, _run_with_known_binning_warning_suppressed(lambda: mc.UserDefined(data, bins=upper_bounds)))


def unclassed_bins(data, bins):
    data = _clean_numeric_data(data)
    return np.array([float(np.min(data)), float(np.max(data))])
# ============================================================
# Divide the data range (max - min) into equal-sized intervals.
# Each bin has the same numeric width.
# ============================================================
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


# ============================================================
# Bin sizes grow exponentially (powers of 2). 
# ============================================================
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

# ============================================================
# Each bin boundary grows geometrically from the minimum value.
# The ratio between consecutive bins is constant.
# ============================================================
def geometric_interval(data, bins):
    minv = data.min()
    maxv = data.max()
    if minv <= 0:
        positive = data[data > 0]
        if len(positive) > 0:
            minv = float(np.min(positive))
        else:
            # just avoid divide by 0
            minv = 1e-9
    ratio = (maxv / minv) ** (1.0 / bins)
    edges = [minv]
    i = 1
    while i < bins:
        edges.append(minv * (ratio ** i))
        i += 1
    edges.append(maxv)
    return np.array(edges)


# ============================================================
# Place breaks where data differences between consecutive values are the largest. Captures sudden jumps in sorted data.
# ============================================================
def maxbreaks_bins(data, bins):
    arr = np.sort(data)
    # get the difference between two consecutive data
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


# ============================================================
# Split the dataset so that each bin contains (approximately) the same number of observations.
# ============================================================
def quantile_bins(data, bins):
    edges = []
    qs = np.linspace(0, 1, bins + 1)
    i = 0
    while i < len(qs):
        q = qs[i]
        edges.append(np.quantile(data, q))
        i += 1
    return np.array(edges)


# ============================================================
# Use quartiles (Q1, median, Q3) and IQR rule to define edges.
# ============================================================
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


# ============================================================
# Create bins based on mean ± k * standard deviation.
# ============================================================
def stdev_bins(data, bins, mean_as_boundary=True, sdfactor=1.0):
    mu = np.mean(data)
    sigma = np.std(data)
    edges = []

    if mean_as_boundary:
        # Variant 1: mean is a boundary 
        mid = bins // 2
        i = 0
        while i <= bins:
            edge = mu + (i - mid) * sdfactor * sigma
            edges.append(edge)
            i += 1

    else:
        # Variant 2: mean is at the center → must be odd number of bins
        if bins % 2 == 0:
            raise ValueError('Variant 2 only works for odd bin count.')
        mid = bins // 2
        i = 0
        while i <= bins:
            edge = mu + (i - mid - 0.5) * sdfactor * sigma
            edges.append(edge)
            i += 1

    return np.array(edges)

# ============================================================
# Recursive splitting for heavy-tailed distributions.
# Each iteration splits values above the mean until uniform.
# ============================================================
def headtail_bins(data):
    breaks = []
    x = np.sort(data)
    while len(x) > 1:
        mean_val = np.mean(x)
        breaks.append(mean_val)
        x = x[x > mean_val]
        #avoid infinity loop
        if len(breaks) > 20:
            break
    edges = [data.min()]
    sorted_breaks = sorted(breaks)
    s = 0
    while s < len(sorted_breaks):
        edges.append(sorted_breaks[s])
        s += 1
    edges.append(data.max())

    uniq = []
    u = 0
    while u < len(edges):
        if edges[u] not in uniq:
            uniq.append(edges[u])
        u += 1
    return np.array(uniq)


# ============================================================
# Chooses rounded, human-friendly intervals that cover the data range.
# ============================================================
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


# ============================================================
# To be confirmed
# Minimizes within-class variance and maximizes between-class variance.
# ============================================================
def natural_breaks(data, bins):
    data = np.sort(np.array(data, dtype=float))
    n = len(data)
    if n == 0 or bins < 1:
        return np.array([])
    if bins >= n:
        return np.unique(data)

    lower_class_limits = np.zeros((n + 1, bins + 1), dtype=int)
    variance_combinations = np.full((n + 1, bins + 1), np.inf)

    # initialize for one class
    i = 1
    while i <= n:
        variance_combinations[i][1] = np.var(data[:i]) * (i - 1)
        lower_class_limits[i][1] = 1
        i += 1

    # dynamic programming
    k = 2
    while k <= bins:
        i = k
        while i <= n:
            best_var = np.inf
            best_m = -1
            m = k - 1
            while m < i:
                group = data[m:i]
                ssd = np.var(group) * (len(group) - 1)
                total_var = variance_combinations[m][k - 1] + ssd
                if total_var < best_var:
                    best_var = total_var
                    best_m = m
                m += 1
            variance_combinations[i][k] = best_var
            lower_class_limits[i][k] = best_m
            i += 1
        k += 1

    k = bins
    kclass = [data[-1]]
    count_num = n
    while k > 1:
        idx = int(lower_class_limits[count_num][k])
        kclass.append(data[idx - 1])
        count_num = idx
        k -= 1
    kclass.append(data[0])
    kclass = sorted(list(set(kclass)))
    return np.array(kclass)


def resiliency_bins(data, bins):
    data = np.sort(_clean_numeric_data(data))
    candidate_methods = [
        mc_equal_interval,
        mc_quantile_bins,
        mc_pretty_bins,
        mc_maxbreaks_bins,
        mc_natural_breaks,
        mc_ckmeans_bins,
    ]

    assignment_rows = []
    for method in candidate_methods:
        try:
            edges = method(data, bins)
            assignments = _digitize_assignments(data, edges)
            if assignments is not None and len(assignments) == len(data):
                assignment_rows.append(assignments)
        except Exception:
            pass

    if not assignment_rows:
        return mc_quantile_bins(data, bins)

    matrix = np.vstack(assignment_rows)
    consensus = []
    i = 0
    while i < matrix.shape[1]:
        vals, counts = np.unique(matrix[:, i], return_counts=True)
        consensus.append(int(vals[np.argmax(counts)]))
        i += 1

    consensus = np.maximum.accumulate(np.array(consensus, dtype=int))
    edges = [float(data[0])]
    i = 1
    while i < len(data):
        if consensus[i] != consensus[i - 1]:
            edges.append(float(data[i]))
        i += 1
    edges.append(float(data[-1]))

    edges = _unique_sorted_edges(edges)
    if edges.size < 2:
        return mc_quantile_bins(data, bins)
    return edges


BIN_METHODS = {
    "Unclassed": unclassed_bins,
    "Defined Interval": mc_defined_interval,
    "Equal Interval": mc_equal_interval,
    "Exponential": exponential_bins,
    "Geometric Interval": geometric_interval,
    "Maximum Breaks": mc_maxbreaks_bins,
    "Quantile": mc_quantile_bins,
    "Pretty Breaks": mc_pretty_bins,
    "Natural Breaks": mc_natural_breaks,
    "Fisher-Jenks": mc_ckmeans_bins,
    "Percentile": mc_percentile_bins,
    "Resiliency": resiliency_bins,
    "Box Plot": mc_boxplot_bins,
    "Head/Tail Breaks": mc_headtail_bins,
    "Standard Deviation": mc_stdev_bins,
}
