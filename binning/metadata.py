import numpy as np
import pandas as pd

def bin_metadata(raw_data, bin_edges):
    # Ensure unique, sorted edges (preserve exact manual edges)
    bin_edges = np.array(sorted(set(bin_edges)), dtype=float)


    # Assign each value to the correct bin
    bin_assignments = np.digitize(raw_data, bin_edges, right=True) - 1

    # Count how many data points fall into each bin
    bin_sizes = {}
    i = 0
    while i < len(bin_assignments):
        idx = int(bin_assignments[i])
        if idx in bin_sizes:
            bin_sizes[idx] = bin_sizes[idx] + 1
        else:
            bin_sizes[idx] = 1
        i += 1

    # Sort by bin index
    sorted_keys = sorted(bin_sizes.keys())
    sorted_bin_sizes = {}
    i = 0
    while i < len(sorted_keys):
        key = sorted_keys[i]
        sorted_bin_sizes[key] = bin_sizes[key]
        i += 1

    # Build output dictionary
    result = {}
    result["rawData"] = raw_data
    result["dataRange"] = [float(np.min(raw_data)), float(np.max(raw_data))]
    result["binCount"] = len(bin_edges) - 1

    bin_breaks = []
    i = 0
    while i < len(bin_edges):
        bin_breaks.append(float(bin_edges[i]))
        i += 1
    result["binBreaks"] = bin_breaks

    result["binSizes"] = sorted_bin_sizes

    # Convert bin assignments to a list
    bin_list = []
    i = 0
    while i < len(bin_assignments):
        bin_list.append(int(bin_assignments[i]))
        i += 1
    result["dataBinAssignments"] = bin_list

    return result
