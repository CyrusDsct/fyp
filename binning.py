import numpy as np
import pandas as pd

#find file for importing csv values
#csv folder is expected to be located in the same place as this python file
#csv files are expected to be in the csv folder
filename = input(
    "Input the name of the csv file to be used in this analysis.\n"
    "Do not use any folder prefixes or file type suffixes.. (e.g.: 'air_pollution', not 'csv/air_pollution.csv').\n"
)
filename = "csv/" + filename + ".csv"
dataset = pd.read_csv(filename)
print(dataset.to_string()) #for checking

#what is the expected format for the csv? column 1 is location and column 2 is value?
value_col = dataset.columns[1]
max_data = dataset[value_col].max()
min_data = dataset[value_col].min()
num_data = dataset.shape[0]
values = dataset[value_col].values
sorted_values = np.sort(values)

# max_data = dataset[dataset.columns[1]].max()
# min_data = dataset[dataset.columns[1]].min()
print("Maximum value in dataset: " + str(max_data))
print("Minimum value in dataset: " + str(min_data))

#input number of bins
num_bins = input("How many bins are in this chloropleth map? ")
while not num_bins.isdigit():
    num_bins = input("Please enter an integer number of bins. ")
num_bins = int(num_bins)

#definition: a value is sorted into a bin if its value is min <= x <max
manual_bins = np.empty((num_bins, 2))

#input bin ranges
for i in range(num_bins):
    start = input("Input the starting value of bin #" + str(i) + ". ")
    while True:
        try:
            start_val = float(start)
            break
        except ValueError:
            start = input("Please enter a numerical value for the bin's starting value. ")
    manual_bins[i, 0] = start_val

    end = input("Input the end value of bin #" + str(i) + ". ")
    while True:
        try:
            end_val = float(end)
            break
        except ValueError:
            end = input("Please enter a numerical value for the bin's end value. ")
    manual_bins[i, 1] = end_val

num_data = dataset.shape[0]
sorted_data = dataset.sort_values(by=dataset.columns[1])

#available variables: num_data, max_data, min_data, sorted dataframe

#find bins using all binning methods
#put into functions? store in array or dataframe?

# methods = [
#     "equal",
#     "geometric",
#     "exponential",
#     "quantile",
#     "percentile",
#     "boxplot",
#     "stdev",
#     "maxbreaks",
#     "natbreaks",
#     "ck",
#     "htbreaks", #may not include as it is for two bins only
#     "resiliency" #how to implement???
# ]

method_bins = {}

#equal
def equal_bins(minimum, maximum, bins):
    interval = float(maximum - minimum) / bins
    edges = [minimum + i * interval for i in range(bins + 1)]
    result = np.empty((bins, 2))
    for i in range(bins):
        result[i, 0] = edges[i]
        result[i, 1] = edges[i + 1]
    return result
    

#geometric

#exponential
#num_data in nth bin = x^(nth bin) - x^(n-1th bin)
#reverse exponential

#quantile
def quantile_bins(data, bins):
    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.quantile(data, quantiles)
    result = np.empty((bins, 2))
    for i in range(bins):
        result[i, 0] = edges[i]
        result[i, 1] = edges[i + 1]
    return result

#percentile

def percentile_bins(num_data, bins):
    # To be implemented
    pass

#box plot

#standard deviation (stdev)

#maximum breaks (maxbreaks)
def maxbreaks_bins(data, bins):
    arr = np.sort(data)
    diffs = arr[1:] - arr[:-1]
    if len(diffs) < bins:
        edges = np.array([arr[0], arr[-1]])
    else:
        max_indices = np.argpartition(diffs, -bins)[-bins:]
        max_indices = np.sort(max_indices)
        edges = np.concatenate(([arr[0]], arr[max_indices + 1], [arr[-1]]))
    result = np.empty((bins, 2))
    for i in range(bins):
        result[i, 0] = edges[i]
        result[i, 1] = edges[i + 1]
    return result

#natural breaks (natbreaks)
#ck means (ck)
#head tail breaks (htbreaks) #may not include as it is for two bins only
#resiliency? #how to implement???

#go through all bins to find difference

#output most similar binning method
#output bins for comparison

#graph to show data distribution with manual + other bins?
#bar? use arpit's thing? ???

method_bins['equal'] = equal_bins(min_data, max_data, num_bins)
method_bins['quantile'] = quantile_bins(values, num_bins)
method_bins['maxbreaks'] = maxbreaks_bins(values, num_bins)


#similarity part (temp)
def bin_similarity(manual, auto):
    overlap = 0
    for m, a in zip(manual, auto):
        start = max(m[0], a[0])
        end = min(m[1], a[1])
        overlap += max(0, end - start)

    manual_total = np.sum(manual[:,1] - manual[:,0])
    return overlap / manual_total if manual_total > 0 else 0

similarity_result = []
for method, bins in method_bins.items():
    sim = bin_similarity(manual_bins, bins)
    similarity_result.append((method, sim))

similarity_result.sort(key=lambda x: -x[1])
print()
for method, score in similarity_result:
    print(f"{method} similarity: {score:.3f}")

print("Your input:")
print(manual_bins)

for method, bins in method_bins.items():
    print(f"\n{method} bins:")
    print(bins)