import numpy as np
import pandas as pd

#find file for importing csv values
#csv folder is expected to be located in the same place as this python file
#csv files are expected to be in the csv folder
filename = input("Input the name of the csv file to be used in this analysis. \nDo not use any folder prefixes or file type suffixes.. (e.g.: 'air_pollution', not 'csv/air_pollution.csv'.)")
filename = "csv/"&filename&".csv"
dataset = pd.read_csv(filename)
print(dataset.to_string()) #for checking

#input number of bins
num_bins = input("How many bins are in this chloropleth map?")
while (not(num_bins.isdigit())):
    num_bins = input("Please enter an integer number of bins.")

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

#find bins using all binning methods
#put into functions?
#equal
#geometric
#exponential
#quantile
#percentile
#box plot
#standard deviation
#maximum breaks
#natural breaks
#ck means
#head tail breaks
#resiliency?

#go through all bins to find difference

#output most similar binning method
#output bins for comparison

#graph to show data distribution with manual + other bins?
#bar? use arpit's thing? ???
