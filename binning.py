import numpy as np
import pandas as pd

#find file for importing csv values
#csv folder is expected to be located in the same place as this python file
#csv files are expected to be in the csv folder
filename = input("Input the name of the csv file to be used in this analysis. \n"& \
"Do not use any folder prefixes or file type suffixes.. (e.g.: 'air_pollution', not 'csv/air_pollution.csv'.)")
filename = "csv/"&filename&".csv"
dataset = pd.read_csv(filename)
print(dataset.to_string()) #for checking

#what is the expected format for the csv? column 1 is location and column 2 is value?
max_data = dataset[dataset.columns[1]].max()
min_data = dataset[dataset.columns[1]].min()
print("Maximum value in dataset: " & str(max_data))
print("Minimum value in dataset: " & str(min_data))

#input number of bins
num_bins = input("How many bins are in this chloropleth map?")
while (not(num_bins.isdigit())):
    num_bins = input("Please enter an integer number of bins.")

#definition: a value is sorted into a bin if its value is min <= x <max
num_bins = int(num_bins)
manual_bins = np.empty(num_bins,2)
#input bin ranges
for i in range(num_bins):
    start = input("Input the starting value of bin #" & str(i) &".")
    while (not(start.isdigit())):
        start = input("Please enter a numerical value for the bin's starting value.")
    manual_bins[i,0] = float(start)
    
    end = input("Input the end value of bin #" & str(i) & ".")
    while (not(end.isdigit())):
        end = input("Please enter a numerical value for the bin's end value.")
    manual_bins[i,1] = float(end)


num_data = dataset.shape[0]
sorted_data = dataset.sort_values(by=dataset.columns[1])

#available variables: num_data, max_data, min_data, sorted dataframe

#find bins using all binning methods
#put into functions? store in array or dataframe?
methods = ["equal", 
           "geometric", 
           "exponential", 
           "quantile", 
           "percentile",
           "boxplot",
           "stdev",
           "maxbreaks",
           "natbreaks",
           "ck",
           "htbreaks", #may not include as it is for two bins only
           "resiliency" #how to implement???
           ]
method_bins = np.empty(len(methods),num_bins,2)

#equal
def equal(min, max,bins):
    interval = float(max - min)/bins
    threshold = min
    for i in range(bins):
        method_bins[methods.index("equal"),i,0] = threshold
        threshold = threshold + interval
        method_bins[methods.index("equal"),i,1] = threshold

#geometric

#exponential
#num_data in nth bin = x^(nth bin) - x^(n-1th bin)
#reverse exponential

#quantile
def quantile(num_data, bins):
    interval = num_data/bins
    remainder = num_data%bins
    position = 0
    for i in range(bins):
        method_bins[methods.index("quantile"),i,0] = sorted_data[position]
        position += interval
        if (i>remainder):
            position -= 1
        method_bins[methods.index("quantile"),i,1] = sorted_data[position]
        position += 1

#percentile
def percentile(num_data, bins)

#box plot

#standard deviation (stdev)

#maximum breaks (maxbreaks)
def maxbreaks(bins):
    small = np.array(sorted_data[sorted_data.columns(1)])
    big = np.array(small[1:])
    small = small[:-1]
    diff = big - small
    max_indices = np.argpartition(diff, -bins)[-bins:] #return indices of the n largest elements
    max_indices = max_indices.sort()
    for i in range(bins):
        method_bins[methods.index("maxbreaks"),i,0] = small[max_indices[i]]
        method_bins[methods.index("maxbreaks"),i,1] = big[max_indices[i]]
    

#natural breaks (natbreaks)
#ck means (ck)
#head tail breaks (htbreaks) #may not include as it is for two bins only
#resiliency? #how to implement???

#go through all bins to find difference

#output most similar binning method
#output bins for comparison

#graph to show data distribution with manual + other bins?
#bar? use arpit's thing? ???
