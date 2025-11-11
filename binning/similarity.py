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
    import numpy as np

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
