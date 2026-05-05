import numpy as np

# 1D range
def bin_similarity_1d_range(manual_ranges, auto_ranges):
    len_manual = len(manual_ranges)
    len_auto = len(auto_ranges)
    if len_manual < len_auto:
        n = len_manual
    else:
        n = len_auto

    if n == 0:
        return 0.0

    errors = []
    i = 0
    while i < n:
        m_start = manual_ranges[i][0]
        m_end = manual_ranges[i][1]
        a_start = auto_ranges[i][0]
        a_end = auto_ranges[i][1]

        m_width = m_end - m_start
        a_width = a_end - a_start
        
        # Skip invalid bins
        if m_width > 0:
            diff = abs(a_width - m_width)
            err = diff / m_width * 100
            errors.append(err)

        i += 1

    if len(errors) == 0:
        return 0.0

    total = 0.0
    j = 0
    while j < len(errors):
        total = total + errors[j]
        j += 1

    avg_error = total / len(errors)
    return avg_error


# 1D frequency
def bin_similarity_1d_freq(manual_meta, auto_meta):
    manual_sizes = manual_meta["binSizes"]
    auto_sizes = auto_meta["binSizes"]

    len_manual = len(manual_sizes)
    len_auto = len(auto_sizes)
    if len_manual > len_auto:
        n = len_manual
    else:
        n = len_auto

    if n == 0:
        return 0.0

    errors = []
    i = 0
    while i < n:
        if i in manual_sizes:
            m_size = manual_sizes[i]
        else:
            m_size = 0

        if i in auto_sizes:
            a_size = auto_sizes[i]
        else:
            a_size = 0

        if m_size > 0:
            diff = abs(a_size - m_size)
            err = diff / m_size * 100
            errors.append(err)

        i += 1

    if len(errors) == 0:
        return 0.0

    total = 0.0
    j = 0
    while j < len(errors):
        total = total + errors[j]
        j += 1

    avg_error = total / len(errors)
    return avg_error



# 2D
def bin_similarity_2d(manual_meta, auto_meta):
    # Mean error based on (width × count) area difference
    manual_edges = manual_meta["binBreaks"]
    auto_edges = auto_meta["binBreaks"]
    manual_sizes_map = manual_meta["binSizes"]
    auto_sizes_map = auto_meta["binSizes"]

    manual_ranges = []
    i = 0
    while i < len(manual_edges) - 1:
        manual_ranges.append([manual_edges[i], manual_edges[i + 1]])
        i += 1

    auto_ranges = []
    j = 0
    while j < len(auto_edges) - 1:
        auto_ranges.append([auto_edges[j], auto_edges[j + 1]])
        j += 1

    n_manual = len(manual_ranges)
    n_auto = len(auto_ranges)
    if n_manual < n_auto:
        n = n_manual
    else:
        n = n_auto

    if n == 0:
        return 0.0

    errors = []
    k = 0
    while k < n:
        m_start = manual_ranges[k][0]
        m_end = manual_ranges[k][1]
        a_start = auto_ranges[k][0]
        a_end = auto_ranges[k][1]

        m_width = abs(m_end - m_start)
        a_width = abs(a_end - a_start)

        if k in manual_sizes_map:
            m_size = manual_sizes_map[k]
        else:
            m_size = 0

        if k in auto_sizes_map:
            a_size = auto_sizes_map[k]
        else:
            a_size = 0

        # compute area to calculate 2D similarity part
        m_area = m_width * m_size
        a_area = a_width * a_size

        if m_area > 0:
            diff = abs(a_area - m_area)
            err = diff / m_area * 100
            errors.append(err)

        k += 1

    if len(errors) == 0:
        return 0.0

    total = 0.0
    i = 0
    while i < len(errors):
        total = total + errors[i]
        i += 1

    avg_error = total / len(errors)
    return avg_error

def interval_similarity_details(manual_edges, auto_edges):
    """
    Compare normalized edge positions and bin widths.
    This penalizes methods whose bins have similar widths but are shifted to
    the wrong part of the range.
    """
    try:
        m = np.array(manual_edges, dtype=float)
        a = np.array(auto_edges, dtype=float)

        m = m[np.isfinite(m)]
        a = a[np.isfinite(a)]

        if m.size < 2 or a.size < 2:
            return None

        m = np.unique(np.sort(m))
        a = np.unique(np.sort(a))

        if m.size < 2 or a.size < 2:
            return None

        m_range = float(m[-1] - m[0])
        a_range = float(a[-1] - a[0])
        if m_range <= 0 or a_range <= 0:
            return None

        m_norm = (m - m[0]) / m_range
        a_norm = (a - a[0]) / a_range

        manual_widths = np.diff(m_norm)
        auto_widths = np.diff(a_norm)
        comparable_bins = min(len(manual_widths), len(auto_widths))
        if comparable_bins == 0:
            return None

        width_error = float(np.mean(np.abs(manual_widths[:comparable_bins] - auto_widths[:comparable_bins])))

        manual_internal = m_norm[1:-1]
        auto_internal = a_norm[1:-1]
        comparable_edges = min(len(manual_internal), len(auto_internal))
        edge_error = (
            float(np.mean(np.abs(manual_internal[:comparable_edges] - auto_internal[:comparable_edges])))
            if comparable_edges
            else 0.0
        )

        bin_count_penalty = 1.0 - (abs(len(manual_widths) - len(auto_widths)) / max(len(manual_widths), len(auto_widths), 1))
        combined_error = (0.65 * edge_error) + (0.35 * width_error)
        similarity = max(0.0, 1.0 - combined_error) * max(0.0, bin_count_penalty)
        if not np.isfinite(similarity):
            return None

        return {
            "similarity": float(similarity),
            "manual_norm": m_norm,
            "auto_norm": a_norm,
            "manual_widths": manual_widths,
            "auto_widths": auto_widths,
            "width_error": width_error,
            "edge_error": edge_error,
            "bin_count_penalty": float(bin_count_penalty),
            "combined_error": float(combined_error),
        }

    except Exception:
        return None


def interval_similarity(manual_edges, auto_edges):
    details = interval_similarity_details(manual_edges, auto_edges)
    return details["similarity"] if details else None


def _counts_per_bin(data, edges):
    edges = np.asarray(edges, dtype=float)
    x = np.asarray(data, dtype=float).reshape(-1)
    x = x[np.isfinite(x)]
    counts = np.zeros(max(len(edges) - 1, 0), dtype=int)
    for i, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        if i < len(counts) - 1:
            counts[i] = int(np.sum((x >= left) & (x < right)))
        else:
            counts[i] = int(np.sum((x >= left) & (x <= right)))
    return counts


def frequency_overlap_details(manual_edges, auto_edges, data):
    """
    Compare bin heights as histogram-density overlap.
    Each bin contributes mass=count/total_data_count and height=mass/bin_width.
    The score is the area under min(manual_density, auto_density), in [0, 1].
    """
    try:
        m = np.unique(np.sort(np.asarray(manual_edges, dtype=float)))
        a = np.unique(np.sort(np.asarray(auto_edges, dtype=float)))
        x = np.asarray(data, dtype=float).reshape(-1)
        x = x[np.isfinite(x)]

        if m.size < 2 or a.size < 2 or x.size == 0:
            return None
        if np.any(np.diff(m) <= 0) or np.any(np.diff(a) <= 0):
            return None

        manual_counts = _counts_per_bin(x, m)
        auto_counts = _counts_per_bin(x, a)
        total = float(x.size)

        manual_widths = np.diff(m)
        auto_widths = np.diff(a)
        manual_mass = manual_counts / total
        auto_mass = auto_counts / total
        manual_density = manual_mass / manual_widths
        auto_density = auto_mass / auto_widths

        union_edges = np.unique(np.concatenate([m, a]))
        if union_edges.size < 2:
            return None

        overlap = 0.0
        for left, right in zip(union_edges[:-1], union_edges[1:]):
            width = float(right - left)
            if width <= 0:
                continue
            mid = (left + right) / 2.0
            mi = np.searchsorted(m, mid, side="right") - 1
            ai = np.searchsorted(a, mid, side="right") - 1
            md = manual_density[mi] if 0 <= mi < len(manual_density) and mid <= m[mi + 1] else 0.0
            ad = auto_density[ai] if 0 <= ai < len(auto_density) and mid <= a[ai + 1] else 0.0
            overlap += min(float(md), float(ad)) * width

        overlap = float(np.clip(overlap, 0.0, 1.0))
        return {
            "similarity": overlap,
            "manual_counts": manual_counts,
            "auto_counts": auto_counts,
            "manual_shares": manual_mass,
            "auto_shares": auto_mass,
            "manual_density": manual_density,
            "auto_density": auto_density,
        }

    except Exception:
        return None


def composite_similarity_details(manual_edges, auto_edges, data, interval_weight=0.45, frequency_weight=0.55):
    interval = interval_similarity_details(manual_edges, auto_edges)
    frequency = frequency_overlap_details(manual_edges, auto_edges, data)
    if not interval or not frequency:
        return None

    total_weight = interval_weight + frequency_weight
    if total_weight <= 0:
        return None

    similarity = (
        interval_weight * interval["similarity"] + frequency_weight * frequency["similarity"]
    ) / total_weight
    similarity = float(np.clip(similarity, 0.0, 1.0))
    return {
        "similarity": similarity,
        "interval_similarity": interval["similarity"],
        "frequency_similarity": frequency["similarity"],
        "interval_weight": float(interval_weight),
        "frequency_weight": float(frequency_weight),
        "interval": interval,
        "frequency": frequency,
    }


def composite_similarity(manual_edges, auto_edges, data):
    details = composite_similarity_details(manual_edges, auto_edges, data)
    return details["similarity"] if details else None
    
