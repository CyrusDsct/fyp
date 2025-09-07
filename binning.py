# import numpy as np
# import pandas as pd

# #find file for importing csv values
# #csv folder is expected to be located in the same place as this python file
# #csv files are expected to be in the csv folder
# filename = input(
#     "Input the name of the csv file to be used in this analysis.\n"
#     "Do not use any folder prefixes or file type suffixes.. (e.g.: 'air_pollution', not 'csv/air_pollution.csv').\n"
# )
# filename = "csv/" + filename + ".csv"
# dataset = pd.read_csv(filename)
# print(dataset.to_string()) #for checking


# value_col = input("Please enter the column number containing the data that you would like to bin by. (First column = 1)")
# while(not(value_col.isdigit())):
#     num_bins = input("Please enter an integer number of bins.")
# value_col = dataset.columns[int(column)]
# print("You are binning by "& value_col &".")

# max_data = dataset[value_col].max()
# min_data = dataset[value_col].min()
# num_data = dataset.shape[0]
# values = dataset[value_col].values
# sorted_values = np.sort(values)

# print("Maximum value in dataset: " + str(max_data))
# print("Minimum value in dataset: " + str(min_data))


# #input number of bins
# num_bins = input("How many bins are in this chloropleth map? ")
# while not num_bins.isdigit():
#     num_bins = input("Please enter an integer number of bins. ")
# num_bins = int(num_bins)

# #definition: a value is sorted into a bin if its value is min <= x <max
# manual_bins = np.empty((num_bins, 2))

# #input bin ranges
# for i in range(num_bins):
#     start = input("Input the starting value of bin #" + str(i) + ". ")
#     while True:
#         try:
#             start_val = float(start)
#             break
#         except ValueError:
#             start = input("Please enter a numerical value for the bin's starting value. ")
#     manual_bins[i, 0] = start_val

#     end = input("Input the end value of bin #" + str(i) + ". ")
#     while True:
#         try:
#             end_val = float(end)
#             break
#         except ValueError:
#             end = input("Please enter a numerical value for the bin's end value. ")
#     manual_bins[i, 1] = end_val

# #find bins using all binning methods
# #put into functions? store in array or dataframe?

# # methods = [
# #     "equal",
# #     "geometric",
# #     "exponential",
# #     "quantile",
# #     "percentile",
# #     "boxplot",
# #     "stdev",
# #     "maxbreaks",
# #     "natbreaks",
# #     "ck",
# #     "htbreaks", #may not include as it is for two bins only
# #     "resiliency" #how to implement???
# # ]

# method_bins = {}

# #equal
# def equal_bins(minimum, maximum, bins):
#     interval = float(maximum - minimum) / bins
#     edges = [minimum + i * interval for i in range(bins + 1)]
#     result = np.empty((bins, 2))
#     for i in range(bins):
#         result[i, 0] = edges[i]
#         result[i, 1] = edges[i + 1]
#     return result
    

# #geometric

# #exponential
# #num_data in nth bin = x^(nth bin) - x^(n-1th bin)
# #reverse exponential

# #quantile
# def quantile_bins(data, bins):
#     quantiles = np.linspace(0, 1, bins + 1)
#     edges = np.quantile(data, quantiles)
#     result = np.empty((bins, 2))
#     for i in range(bins):
#         result[i, 0] = edges[i]
#         result[i, 1] = edges[i + 1]
#     return result

# #percentile

# def percentile_bins(num_data, bins):
#     # To be implemented
#     pass

# #box plot

# #standard deviation (stdev)

# #maximum breaks (maxbreaks)
# def maxbreaks_bins(data, bins):
#     arr = np.sort(data)
#     diffs = arr[1:] - arr[:-1]
#     if len(diffs) < bins:
#         edges = np.array([arr[0], arr[-1]])
#     else:
#         max_indices = np.argpartition(diffs, -bins)[-bins:]
#         max_indices = np.sort(max_indices)
#         edges = np.concatenate(([arr[0]], arr[max_indices + 1], [arr[-1]]))
#     result = np.empty((bins, 2))
#     for i in range(bins):
#         result[i, 0] = edges[i]
#         result[i, 1] = edges[i + 1]
#     return result

# #natural breaks (natbreaks)
# #ck means (ck)
# #head tail breaks (htbreaks) #may not include as it is for two bins only
# #resiliency? #how to implement???

# #go through all bins to find difference

# #output most similar binning method
# #output bins for comparison

# #graph to show data distribution with manual + other bins?
# #bar? use arpit's thing? ???

# method_bins['equal'] = equal_bins(min_data, max_data, num_bins)
# method_bins['quantile'] = quantile_bins(values, num_bins)
# method_bins['maxbreaks'] = maxbreaks_bins(values, num_bins)


# #similarity part (temp)
# def bin_similarity(manual, auto):
#     overlap = 0
#     for m, a in zip(manual, auto):
#         start = max(m[0], a[0])
#         end = min(m[1], a[1])
#         overlap += max(0, end - start)

#     manual_total = np.sum(manual[:,1] - manual[:,0])
#     return overlap / manual_total if manual_total > 0 else 0

# similarity_result = []
# for method, bins in method_bins.items():
#     sim = bin_similarity(manual_bins, bins)
#     similarity_result.append((method, sim))

# similarity_result.sort(key=lambda x: -x[1])
# print()
# for method, score in similarity_result:
#     print(f"{method} similarity: {score:.3f}")

# print("Your input:")
# print(manual_bins)

# for method, bins in method_bins.items():
#     print(f"\n{method} bins:")
#     print(bins)
    

# Cyrus's idea
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# --------- assigns each value in raw_data to a bin ---------
def bin_metadata(raw_data, bin_edges):
    bin_assignments = np.digitize(raw_data, bin_edges, right=False) - 1
    bin_assignments[bin_assignments == len(bin_edges) - 1] = len(bin_edges) - 2
    bin_sizes = pd.Series(bin_assignments).value_counts().sort_index()
    return {
        "rawData": raw_data,
        "dataRange": [float(raw_data.min()), float(raw_data.max())],
        "binCount": len(bin_edges) -1,
        "binBreaks": [float(x) for x in bin_edges],
        "binSizes": bin_sizes.to_dict(),
        "dataBinAssignments": bin_assignments.tolist()
    }

# ---------  Binning Algorithms---------
import numpy as np

def equal_interval(data, bins):
    minv, maxv = data.min(), data.max()
    interval = (maxv - minv) / bins
    edges = []
    for i in range(bins + 1):
        edge = minv + i * interval
        edges.append(edge)
    return np.array(edges)

def defined_interval(data, interval):
    minv, maxv = data.min(), data.max()
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
    powers = np.array([2 ** i for i in range(bins)])
    sizes = powers / powers.sum() * N
    sizes = np.round(sizes).astype(int)
    sizes[-1] = N - sizes[:-1].sum()
    sorted_data = np.sort(data)
    breaks = [sorted_data[0]]
    idx = 0
    for size in sizes[:-1]:
        idx += size
        breaks.append(sorted_data[min(idx, N-1)])
    breaks.append(sorted_data[-1])
    return np.unique(breaks)

def geometric_interval(data, bins):
    minv, maxv = data.min(), data.max()
    if minv <= 0:
        minv = np.min(data[data > 0])  
    ratio = (maxv / minv) ** (1/ bins)
    edges = [minv]
    for i in range(1, bins):
        edges.append(minv * (ratio ** i))
    edges.append(maxv)
    return np.array(edges)

def maxbreaks_bins(data, bins):
    arr = np.sort(data)
    diffs = arr[1:] - arr[:-1]
    if len(diffs) < bins -1:
        edges = [arr[0], arr[-1]]
    else:
        max_indices = np.argsort(diffs)[-(bins-1):]
        max_indices = np.sort(max_indices)
        edges = [arr[0]]
        for idx in max_indices:
            edges.append(arr[idx + 1])
        edges.append(arr[-1])
    return np.unique(edges)

def quantile_bins(data, bins):
    edges = [np.quantile(data, q) for q in np.linspace(0, 1, bins + 1)]
    return np.array(edges)

def boxplot_bins(data):
    q1 = np.percentile(data, 25)
    q2 = np.percentile(data, 50)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    edges = [data.min(), lower, q1, q2, q3, upper, data.max()]
    return np.unique(edges)

# def percentile_bins(data, percentiles=[ ]):
#     edges = [data.min()]
#     for p in percentiles:
#         edges.append(np.percentile(data, p))
#     edges.append(data.max())
#     return np.unique(edges)

def stdev_bins(data, bins, mean_as_boundary=True, sdfactor=1.0):
    mu = np.mean(data)
    sigma = np.std(data)
    if mean_as_boundary:
        edges = [mu + (i - bins // 2) * sdfactor * sigma for i in range(bins + 1)]
    else:
        if bins % 2 == 0:
            raise ValueError('Variant 2 only works for odd bin count.')
        mid = bins // 2
        edges = [mu + (i - mid - 0.5) * sdfactor * sigma for i in range(bins + 1)]
    edges = [data.min()] + edges + [data.max()]
    return np.unique(edges)

# def fisher_jenks_bins(data, bins):
#     return quantile_bins(data, bins)

# def ckmeans_bins(data, bins):
#     return quantile_bins(data, bins)

def headtail_bins(data):
    breaks = []
    x = np.sort(data)
    while len(x) > 1:
        mean_val = np.mean(x)
        breaks.append(mean_val)
        x = x[x > mean_val]
        if len(breaks) > 20:
            break  
    edges = [data.min()] + sorted(breaks) + [data.max()]
    return np.unique(edges)

def pretty_bins(data, bins):
    minv, maxv = float(np.min(data)), float(np.max(data))
    step = (maxv - minv) / bins
    mag = 10 ** np.floor(np.log10(step))
    nice_step = np.ceil(step / mag) * mag
    nice_min = np.floor(minv / mag) * mag
    nice_max = np.ceil(maxv /mag) * mag
    edges = [nice_min + i * nice_step for i in range(bins + 1)]
    if edges[-1] < nice_max:
        edges.append(nice_max)
    return np.unique(edges)

# --------- Similarity  ---------
def bin_similarity(manual_ranges, auto_ranges):
    # overlap = 0
    # for m in manual_ranges:
    #     for a in auto_ranges:
    #         start = max(m[0], a[0])
    #         end = min(m[1], a[1])
    #         overlap += max(0, end - start)
    # manual_total = np.sum([m[1] - m[0] for m in manual_ranges])
    # return overlap / manual_total if manual_total > 0 else 0
    
    # #EUCLIDEAN
    # if (manual_ranges.shape == auto_ranges.shape):
    #     differences = manual_ranges-auto_ranges
    # elif (manual_ranges.size > auto_ranges.size):
    #     differences = manual_ranges[:auto_ranges.shape[0]] - auto_ranges
    # else:
    #     differences = manual_ranges - auto_ranges[:manual_ranges.shape[0]]
    # differences = differences**2
    # differences = np.sum(differences)
    # differences = differences ** 0.5
    # return differences

    #NORMALIZED EUCLIDEAN
    if (manual_ranges.shape == auto_ranges.shape):
        differences = 1 - auto_ranges/manual_ranges
    elif (manual_ranges.size > auto_ranges.size):
        differences = 1 - auto_ranges/manual_ranges[:auto_ranges.shape[0]]
    else:
        differences = 1 - auto_ranges[:manual_ranges.shape[0]]/manual_ranges
    #print("subtracted", differences)
    differences = differences**2
    #print("squared", differences)
    differences = np.nan_to_num(differences,nan=0, posinf=0, neginf=0)
    #print("na removed", differences)
    differences = np.sum(differences)
    #print("summed", differences)
    differences = differences ** 0.5
    #print("sqrt", differences)
    return differences

# --------- Input file name (csv) ---------
filename = input("Input the name of the csv file (without folder or .csv):\n")
filename = "csv/" + filename + ".csv"
dataset = pd.read_csv(filename)
print(dataset.to_string())  

value_col = input("Please enter the column number containing the data that you would like to bin by. (First column = 1)")
while(not(value_col.isdigit())):
    num_bins = input("Please enter an integer number of bins.")
value_col = dataset.columns[int(value_col)-1]
print(f"You are binning by {value_col}.")
values = dataset[value_col].values

num_bins = input("How many bins/classes? ")
while not num_bins.isdigit():
    num_bins = input("Please enter an integer number of bins. ")
num_bins = int(num_bins)

print("Input each bin's min and max")
manual_bins = np.empty((num_bins, 2))
for i in range(num_bins):
    while True:
        try:
            start = float(input(f"Bin #{i+1} min: "))
            break
        except ValueError:
            print("Please enter a numeric value.")
    manual_bins[i, 0] = start
    while True:
        try:
            end = float(input(f"Bin #{i+1} max: "))
            break
        except ValueError:
            print("Please enter a numeric value.")
    manual_bins[i, 1] = end

manual_edges = list(sorted(set(manual_bins.flatten())))
try:
    method_bins = {}
    method_bins['Manual'] = bin_metadata(values, manual_edges)
except Exception as e:
    print("Error in Manual bin_metadata:", e)
    exit()

# --------- Start Binning ---------
print("\nRunning all binning methods...\n")
try:
    method_bins['Equal Interval'] = bin_metadata(values, equal_interval(values, num_bins))
    method_bins['Exponential'] = bin_metadata(values, exponential_bins(values, num_bins))
    method_bins['Geometric Interval'] = bin_metadata(values, geometric_interval(values, num_bins))
    method_bins['Maximum Breaks'] = bin_metadata(values, maxbreaks_bins(values, num_bins))
    method_bins['Quantile'] = bin_metadata(values, quantile_bins(values, num_bins))
    method_bins['Box Plot'] = bin_metadata(values, boxplot_bins(values))
    # method_bins['Percentile'] = bin_metadata(values, percentile_bins(values))
    method_bins['Standard Deviation 1'] = bin_metadata(values, stdev_bins(values, num_bins, True, 1.0))
    if num_bins % 2 == 1:
        method_bins['Standard Deviation 2'] = bin_metadata(values, stdev_bins(values, num_bins, False, 1.0))
    # method_bins['Fisher Jenks'] = bin_metadata(values, fisher_jenks_bins(values, num_bins))
    # method_bins['CKMeans'] = bin_metadata(values, ckmeans_bins(values, num_bins))
    # method_bins['Head Tail Breaks'] = bin_metadata(values, headtail_bins(values))
    method_bins['Pretty Breaks'] = bin_metadata(values, pretty_bins(values, num_bins))
except Exception as e:
    print("Error in binning methods:", e)
    exit()

# --------- Similarity  ---------
print("\n--- Similarity to Manual Bins ---")
manual_ranges = manual_bins
similarity = []
for method, meta in method_bins.items():
    auto_ranges = []
    for i in range(len(meta["binBreaks"]) - 1):
        auto_ranges.append([meta["binBreaks"][i], meta["binBreaks"][i + 1]])
    auto_ranges = np.array(auto_ranges)
    sim = bin_similarity(manual_ranges, auto_ranges)
    similarity.append((method, sim))
similarity.sort(key=lambda x: -x[1])
for method, sim in similarity:
    print(f"{method}: {sim:.3f}")

# --------- Output (Graph) ---------
for method, meta in method_bins.items():
    print(f"\n=== {method} ===")
    for i, j in meta.items():
        if i in ['rawData', 'dataBinAssignments']: 
            continue
        print(f'{i}: {j}')
    
    plt.figure(figsize=(8, 4))
    plt.hist(values, bins=30, color='lightgray', edgecolor='black')
    for b in meta["binBreaks"]:
        plt.axvline(b, color='red', linestyle='--')
    plt.title(f"{method} Binning")
    plt.xlabel(value_col)
    plt.ylabel("Count")
    plt.show()

print("\nDone.")
