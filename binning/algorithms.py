import numpy as np

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

# def defined_interval(data, interval):
#     minv = data.min()
#     maxv = data.max()
#     edges = [minv]
#     while edges[-1] < maxv:
#         next_edge = edges[-1] + interval
#         if next_edge >= maxv:
#             edges.append(maxv)
#             break
#         edges.append(next_edge)
#     return np.array(edges)


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
