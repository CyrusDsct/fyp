import pandas as pd
import numpy as np
import os
from binning.metadata import bin_metadata
from binning import algorithms as algo
from binning.similarity import (
    bin_similarity_1d_range,
    bin_similarity_1d_freq,
    bin_similarity_2d,
)
from binning.plotting import plot_all

# The user chooses which column to bin.
# Non-numeric values are ignored.
filename = input("CSV file name (without .csv): ")
dataset = pd.read_csv("csv/" + filename + ".csv")
print(dataset.head())

col_idx = int(input("Column number (starting from 1): ")) - 1
col = dataset.columns[col_idx]

values = pd.to_numeric(dataset[col], errors="coerce").dropna().values
print("Loaded", len(values), "valid numeric values from column '" + str(col) + "'")

# Input manual bins
num_bins = int(input("How many bins/classes? "))
manual_bins = np.empty((num_bins, 2))
i = 0
while i < num_bins:
    manual_bins[i, 0] = float(input("Bin #" + str(i + 1) + " min: "))
    manual_bins[i, 1] = float(input("Bin #" + str(i + 1) + " max: "))
    i += 1

# convert manual range to an unrepeated array
flat_edges = list(manual_bins.flatten())
manual_edges = sorted(set(flat_edges))
method_bins = {"Manual": bin_metadata(values, manual_edges)}

#Compute all automatic binning methods
method_bins["Equal Interval"] = bin_metadata(values, algo.equal_interval(values, num_bins))
method_bins["Exponential"] = bin_metadata(values, algo.exponential_bins(values, num_bins))
method_bins["Geometric Interval"] = bin_metadata(values, algo.geometric_interval(values, num_bins))
method_bins["Maximum Breaks"] = bin_metadata(values, algo.maxbreaks_bins(values, num_bins))
method_bins["Quantile"] = bin_metadata(values, algo.quantile_bins(values, num_bins))
method_bins["Box Plot"] = bin_metadata(values, algo.boxplot_bins(values))
method_bins["Standard Deviation 1"] = bin_metadata(values, algo.stdev_bins(values, num_bins, True, 1.0))
if num_bins % 2 == 1:
    method_bins["Standard Deviation 2"] = bin_metadata(values, algo.stdev_bins(values, num_bins, False, 1.0))
method_bins["Head-Tail Breaks"] = bin_metadata(values, algo.headtail_bins(values))
method_bins["Pretty Breaks"] = bin_metadata(values, algo.pretty_bins(values, num_bins))
method_bins["Natural Breaks"] = bin_metadata(values, algo.natural_breaks(values, num_bins))

manual_meta = method_bins["Manual"]
manual_sizes = manual_meta["binSizes"]


# Range Error  = difference in bin width
# Count Error  = difference in number of elements
# 2D Error     = area difference (width × density)
summary_rows = []
avg_range_list = []
avg_freq_list = []
avg_2d_list = []

for name in method_bins:
    meta = method_bins[name]

    auto_ranges = []
    i = 0
    while i < len(meta["binBreaks"]) - 1:
        start_val = meta["binBreaks"][i]
        end_val = meta["binBreaks"][i + 1]
        auto_ranges.append([start_val, end_val])
        i += 1
        
    #The average proportional difference between manual and automatic bin widths (ranges).
    avg_range_err = bin_similarity_1d_range(manual_bins, auto_ranges)
    #The average proportional difference in counts per bin.
    avg_freq_err = bin_similarity_1d_freq(manual_meta, meta)
    #Comparing the area difference between each pair of bins
    avg_2d_err = bin_similarity_2d(manual_meta, meta)

    # Save row for export
    row = {
        "Method": name,
        "Avg Range Error(%)": round(avg_range_err, 2),
        "Avg Count Error(%)": round(avg_freq_err, 2),
        "Avg 2D Error(%)": round(avg_2d_err, 2)
    }
    summary_rows.append(row)

    avg_range_list.append([name, avg_range_err])
    avg_freq_list.append([name, avg_freq_err])
    avg_2d_list.append([name, avg_2d_err])

# Per-bin report
detail_rows = []
for name in method_bins:
    meta = method_bins[name]
    auto_edges = meta["binBreaks"]
    auto_sizes = meta["binSizes"]

    method_avg_range = 0.0
    method_avg_count = 0.0
    method_avg_2d = 0.0

    r_idx = 0
    while r_idx < len(summary_rows):
        if summary_rows[r_idx]["Method"] == name:
            method_avg_range = summary_rows[r_idx]["Avg Range Error(%)"]
            method_avg_count = summary_rows[r_idx]["Avg Count Error(%)"]
            method_avg_2d = summary_rows[r_idx]["Avg 2D Error(%)"]
            break
        r_idx += 1

    max_bins = max(len(manual_bins), len(auto_edges) - 1)
    i = 0
    while i < max_bins:
        # Manual bin info
        if i < len(manual_bins):
            m_start = manual_bins[i][0]
            m_end = manual_bins[i][1]
            if i in manual_sizes:
                m_size = manual_sizes[i]
            else:
                m_size = 0
        else:
            m_start = np.nan
            m_end = np.nan
            m_size = 0

        # Auto bin info
        if i < len(auto_edges) - 1:
            a_start = auto_edges[i]
            a_end = auto_edges[i + 1]
            if i in auto_sizes:
                a_size = auto_sizes[i]
            else:
                a_size = 0
        else:
            a_start = np.nan
            a_end = np.nan
            a_size = 0

        #Per-bin Range Error 
        if not np.isnan(m_start) and not np.isnan(a_start):
            m_width = abs(m_end - m_start)
            a_width = abs(a_end - a_start)
            if m_width > 0:
                diff_width = abs(a_width - m_width)
                range_err = diff_width / m_width * 100
            else:
                range_err = np.nan
        else:
            range_err = np.nan

        #Per-bin Count Error 
        diff_count = abs(a_size - m_size)
        if m_size > 0:
            count_err = diff_count / m_size * 100
        else:
            count_err = np.nan

        # Build record ---
        record = {}
        record["Method"] = name
        record["Bin Number"] = i + 1

        if not np.isnan(a_start):
            record["Bin Start"] = round(a_start, 6)
        else:
            record["Bin Start"] = "-"

        if not np.isnan(a_end):
            record["Bin End"] = round(a_end, 6)
        else:
            record["Bin End"] = "-"

        if not np.isnan(range_err):
            record["Range Error(%)"] = round(range_err, 2)
        else:
            record["Range Error(%)"] = "-"

        record["Manual_Count"] = m_size
        record["Auto_Count"] = a_size
        record["Difference"] = a_size - m_size

        if not np.isnan(count_err):
            record["Count Error(%)"] = round(count_err, 2)
        else:
            record["Count Error(%)"] = "-"

        record["Avg Range Error(%) (method)"] = method_avg_range
        record["Avg Count Error(%) (method)"] = method_avg_count
        record["Avg 2D Error(%) (method)"] = method_avg_2d

        # Append record to full list
        detail_rows.append(record)
        i += 1


# print result and save it
print("\n--- 1D Range Error (%) ---")
i = 0
while i < len(avg_range_list):
    print(avg_range_list[i][0] + ": " + str(round(avg_range_list[i][1], 2)))
    i += 1

print("\n--- 1D Frequency Error (%) ---")
i = 0
while i < len(avg_freq_list):
    print(avg_freq_list[i][0] + ": " + str(round(avg_freq_list[i][1], 2)))
    i += 1

print("\n--- 2D Overall Error (%) ---")
i = 0
while i < len(avg_2d_list):
    print(avg_2d_list[i][0] + ": " + str(round(avg_2d_list[i][1], 2)))
    i += 1

os.makedirs("output", exist_ok=True)

# Export summary to 'output' folder
summary_df = pd.DataFrame(summary_rows)
summary_path = "output/" + filename + "_methods_summary.csv"
summary_df.to_csv(summary_path, index=False)

detail_df = pd.DataFrame(detail_rows)
detail_path = "output/" + filename + "_bin_report_full.csv"
detail_df.to_csv(detail_path, index=False)

print("\nSaved summaries to:")
print("  " + summary_path)
print("  " + detail_path)

plot_all(values, method_bins)
