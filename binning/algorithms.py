import numpy as np
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

    uniq = []
    r = 0
    while r < len(new_edges):
        if new_edges[r] not in uniq:
            uniq.append(new_edges[r])
        r += 1
    return np.array(uniq)


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
