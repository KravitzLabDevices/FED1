'''
Author: Ilona Szczot
Date: July 15 2016
Purpose: The application processes multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse. It extracts only common full 12 hours daytime and nighttime intervals, in order
to later compare data sets from equal sized nighttime and daytime periods. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time for calculating the eating rate
(between pellets per 1 min and per 2 hours).Then, according to the given parameters, the application plots a bar chart
with the results of analyzis and standard errors, and a statistical significance(ttest), if there is one
('*' for p<0.05, '**' for p<0.01). In addition, the program prints out the values in the console.
'''


'''
Requirements: Anaconda(Python2.7)
(for Python 3.5 change imports(line 28,29) to tkinter and filedialog)
Tested on Windows7.
'''

import os, sys
import fnmatch
from Tkinter import *
import tkFileDialog
import matplotlib.pyplot as plt
import matplotlib.dates as md
import datetime as dt
from datetime import timedelta
import numpy as np
from scipy.stats import ttest_ind
import math
import csv

# default application variables in the initial options window  
fields = ['Time in seconds', 'Lights out hour', 'Lights on hour']     
variables = ['3600','15','3']   # 30min interval in seconds(1800sec), lights out at 3pm, lights on at 3am

# function to pop up the information about the problem
def popup_msg(message):
    popup = Tk()
    popup.wm_title("!")
    label = Label(popup, text=message)
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Ok", command = lambda: sys.exit())
    B1.pack()
    popup.mainloop()

# function to set variables according to the user input
def fetch(root,entries):
    for i in range(len(entries)):
        variables[i] = entries[i][1].get()
    root.quit()

# function to create the options window with default variables displayed
def take_options(root, fields, variables):
    entries = list()
    for i in range(len(fields)):
        row = Frame(root)
        lab = Label(row, width=20, text=fields[i], anchor='w')
        ent = Entry(row)
        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)
        ent.pack(side=RIGHT, expand=YES, fill=X)
        ent.insert(20, variables[i])
        entries.append((fields[i], ent))        
    return entries

# create option window with entry fields 
option_window = Tk()
option_window.title('Options')
ents = take_options(option_window, fields, variables)
option_window.bind('<Return>', (lambda event, e=ents: fetch(e)))   
b1 = Button(option_window, text='OK', command=(lambda e=ents: fetch(option_window, e)))
b1.pack(side=RIGHT, padx=5, pady=5)
b2 = Button(option_window, text='Quit', fg='red',command=sys.exit)
b2.pack(side=LEFT, padx=5, pady=5)
option_window.mainloop()

# Set application constants accordingly
# verify user input
try:
    bin = int(variables[0])      
    lights_out = int(variables[1])     
    lights_on = int(variables[2])   
    if bin < 60 or bin > 7200 or lights_out <= 0 or lights_out >= 24 or lights_on <= 0 or lights_on >= 24:
        popup_msg("Time bin has to be 60-7200sec\nHours in 24hour format")
except:
    popup_msg("Wrong input")

# display folders through Tkinter, tkFileDialog
# set the path to the folder according to users choice
src = tkFileDialog.askdirectory()

########################################## functions

# Converts timestamp into a number
def convertTime(date):
	return md.date2num(dt.datetime.strptime(date, "%m/%d/%Y %H:%M:%S")) 
    
# get data from a file (only the first column=date)
# takes a csv file as an argument
# returns a list of datetime elements( all timestamps) from this file
def get_data(filename):
    my_cols = list()
    with open(filename) as csvfile:
        the_data = csv.reader(csvfile, delimiter=',')
        try:
            for line in the_data:           
                my_cols.append(md.num2date(convertTime(line[0]), tz=None))
        except:
            popup_msg("First column of your file could not be converted from date: %m/%d/%Y %H:%M:%S")
    # skip the first timestamp=irrelevant       
    return my_cols[1:]
    
# returns a list of lists
# each list contains all timestamps from a single csv file from the folder (e.g. 8files=8lists within returned list)
# it takes a path to the folder as an argument
def read_all(path):
    try:        # if user manually points to nonexistent folder
        # os.listdir(path) lists all files in the directory form the given path
        directory = os.listdir(path)
        list_all = list()
        for file in directory:
            # search only those that are csv files
            if fnmatch.fnmatch(file, '*.csv'):               
                # get_data(filename) function will now read all of the timestamps from one fille
                # and add it in the form of list to the list_all
                list_all.append(get_data(os.path.join(path, file)))
    except:
        popup_msg("No file was read")
    # check if any data was read
    if len(list_all) == 0:
        popup_msg("No data was read")
    return list_all

# returns the earliest common date and latest common date
# we are interested only in the common time period
# takes a list of lists of timestamps as an argument (result of read_all function)
def get_border_times(list_all):
    # append only the first timestamps from each file
    all_start_dates = [min(file) for file in list_all]
    # append only the last timestamps from each file
    all_end_dates = [max(file) for file in list_all]

    # the latest date in all_start_dates will be the earliest common date    
    earliest = max(all_start_dates)     # find the earliest common

    # the earliest date in all_end_dates will be the latest common date   
    latest = min(all_end_dates)     # find the latest common

    return earliest, latest

# returns data from start to end date only (a list of lists of timestamps)
# takes as an argument a list of lists of timestamps (result of read_all function)
# and the earliest and latest common dates we want to plot (results of get_border_times function)
def extract_times(list_all, start_date, end_date):
    extracted_data = list()  
    for el in list_all:
        start_index = 0
        end_index = 0
        for timestamp in el:
            # as soon as it finds start date, it stops iterating further
            if timestamp >= start_date and timestamp <= end_date:
                # get the index for the start date in that list
                start_index = el.index(timestamp)
                break
        for timestamp in reversed(el):
            # as soon as it finds end date, it stops iterating
            if timestamp <= end_date and timestamp >= start_date:
                # get the index for the end date in that list
                end_index = el.index(timestamp) + 1     # add 1 for the list slicing to include that index
                break
        # append only lists from start to end date
        extracted_data.append(el[start_index:end_index])      
    return extracted_data   

# returns list of start-end tuples representing given interval of nighttime hours (number format)
# takes as an argument: a single list of timestamps(one sample file), start_hour=beginning of nighttime, 
# end_hour=end of nighttime(24hours:1-00), and start and end time of a whole plot(data from: get_border_times(list_all))
def get_intervals(list_of_timestamps, start_hour, end_hour, earliest, latest):
    dates_from_file = list()
    interval = list()
    date2num_begin = md.date2num(earliest)      # beginning of plot      
    date2num_end = md.date2num(latest)          # end of plot
    # check how many dates(calendar days) are in the fed
    for el in list_of_timestamps:
        if el.date() not in dates_from_file:
            dates_from_file.append(el.date())     
    # for each date in fed, create start_hour-end_hour pair of night interval (datetime, number format)
    if start_hour >= 12:
        for i in range(len(dates_from_file)):
            # start interval
            date2num = md.date2num(dt.datetime.combine(dates_from_file[i], dt.time(hour=start_hour)))
            if (i+1) < len(dates_from_file):        # makes sure it is not the last inteval
                # end interval
                date2num_next = md.date2num(dt.datetime.combine(dates_from_file[i+1], dt.time(hour=end_hour)))
            else:       ## it means it is the last interval
                # if there is only one day on the list check if the start interval is later than beginning 
                if len(dates_from_file) == 1:
                    temp0 = date2num if date2num >= date2num_begin else date2num_begin 
                    interval.append((temp0, date2num_end))
                    break
                else:
                    if date2num <= date2num_end: 
                        interval.append((date2num, date2num_end))
                    break
            # if the start interval hour is later than first timestamp, set the beginning of interval to beginning of plot
            if date2num >= date2num_begin:
                temp0 = date2num
                # if the next date is in the list, set it to the end of nighttime, if not set the end of plot to be the end of nighttime
                temp1 = date2num_next if date2num_next <= date2num_end else date2num_end
            # if the start hour on that date  was earlier than the plot, set the first available to be the beginning of nighttime     
            else:
                temp0 = date2num_begin
                temp1 = date2num_next if date2num_next <= date2num_end else date2num_end
            interval.append((temp0,temp1))
    else:   # lights out hour before noon
        for i in range(len(dates_from_file)):
            # start interval
            date2num = md.date2num(dt.datetime.combine(dates_from_file[i], dt.time(hour=start_hour)))
            # end interval
            date2num_next = md.date2num(dt.datetime.combine(dates_from_file[i], dt.time(hour=end_hour)))
            if (i == len(dates_from_file) - 1) or i == 0:   # for the last interval or if it is the only one
                # if the start interval hour is later than first timestamp, set the beginning of interval to beginning of plot
                if date2num >= date2num_begin:
                    temp0 = date2num
                    # if the next date is in the list, set it to the end of nighttime, if not set the end of plot to be the end of nighttime
                    temp1 = date2num_next if date2num_next <= date2num_end else date2num_end
                # if the start hour on that date  was earlier than the plot, set the first available to be the beginning of nighttime     
                else:
                    temp0 = date2num_begin
                    temp1 = date2num_next if date2num_next <= date2num_end else date2num_end
                interval.append((temp0,temp1))

            else:   # if it is not the last or first interval
                interval.append((date2num,date2num_next))
        
    return interval
# returns daytime intervals based on nights 
# it takes as arguments start and end time of a whole plot(data from: get_border_times(list_all))=earliesr, latest
# and nighttime intervals(result of get_intervals)
def reverse_intervals(earliest, latest, interval):
    daytime = list()
    earliest = md.date2num(earliest)      # beginning of plot, convert to date     
    latest = md.date2num(latest)
    for i in range(len(interval)):
        if (i+1) < len(interval):   # if it is not the last interval and there are more than 1 intervals
            if i == 0:      # if it is the first one
                if earliest < interval[i][0]:                 
                    daytime.append((earliest, interval[i][0]))               
                    daytime.append((interval[i][1],interval[i+1][0]))
                else:
                    daytime.append((interval[i][1],interval[i+1][0]))
            else:
                daytime.append((interval[i][1], interval[i+1][0]))
        else:   # it is last one
            if len(interval) == 1:  # if there was only one 
                if earliest < interval[i][0]:
                    daytime.append((earliest, interval[i][0]))
                if interval[i][1] < latest:
                    daytime.append((interval[i][1], latest))
            else:   # last but there were more than one
                if interval[i][1] < latest:
                    daytime.append((interval[i][1], latest))
    return daytime

# look for full 12 hour night periods
def get_12h_intervals(interval):
    my_intervals = list()
    for el in interval:
        # convert time number to date in order to compare, 43200sec=12hours
        if (md.num2date(el[1]) - md.num2date(el[0])).total_seconds() == 43200:
            my_intervals.append(el)
    return my_intervals
  
# returns average eating rate and standard error, and data to error(for ttest) 
# takes as argument extracted data(list of common timestamps for all files) and result of get_12h_intervals function
def get_nights_rate(extracted_data, full_nights):
    only_nights = []    # divide extracted data into single night (or day) intervals
    for el in full_nights:
        start, end = el
        only_nights.append(extract_times(extracted_data, md.num2date(start), md.num2date(end)))
    all_bins = []   # fill the bins for each night (or day) separately
    for el in only_nights:
        the_oldest, the_newest = get_border_times(el)
        how_many_bins = get_number_of_bins(the_newest, the_oldest,  bin)
        all_bins.append(fill_bins(how_many_bins, el, the_oldest, bin))
    # calculate rates for each night/day
    rates_per_night = [get_rate(all_bins[i]) for i in range(len(all_bins))]
    # extract from the above tuples only rates
    rates = [rates_per_night[i][0] for i in range(len(rates_per_night))]
    avg = sum(rates)/len(rates_per_night)   # calculate total average rate
    # concatenate all data (from all nights or days) for std error and ttest
    data2err = []
    for el in rates_per_night:
        data2err.extend(el[1])
    return avg, my_std_err(data2err), data2err

# returns full 12hour nights and days timestamps, where number of days = number of nights
def get_days_and_nights(extracted_data, full_nights, full_days):
    # make full nights equal full days
    while (len(full_days) != len(full_nights)):
        if len(full_days) > len(full_nights):
            del full_days[-1]
        else:
            del full_nights[-1]
    
    start = full_nights[0][0] if full_nights[0][0] < full_days[0][0] else full_days[0][0]
    end = full_nights[-1][1] if full_nights[-1][1] > full_days[-1][1] else full_days[-1][1]
    return extract_times(extracted_data, md.num2date(start), md.num2date(end))
    

# function to find number of bins given 2 times and a desired time interval  
# time difference is a timedelta type, it is first converted to seconds and divided by interval in seconds 
def get_number_of_bins (latest, earliest, tinterval):
    return int(math.floor((latest-earliest).total_seconds()/tinterval))
    
# fill each bin(number of bins=number of time intervals) according to the data from each file 
# returns list of lists of bins (number of lists=number of files)  
# takes as arguments number of all intervals(bins calculated from get_number_of_bins function), 
# list of lists of timestamps (result of extract_times function), earliest common date, and time interval(e.g. 1hour=3600sec) in seconds  
def fill_bins(intervalsNo, list_all, earliest, interval):
    # create empty bins accorcing to the number of intervals
    list_of_bins = [np.zeros(intervalsNo) for i in range(len(list_all))]
    # fill the empty bins with timestamp count
    for i in range(len(list_all)):
        for j in range(len(list_all[i])):            
            tick = get_number_of_bins(list_all[i][j], earliest, interval)
            if tick-1 < intervalsNo:
                # subtract 1 from index=tick, because indexes start from 0
                list_of_bins[i][tick-1] += 1
    return list_of_bins

# returns  a tuple of average rate and data to calculate std error
def get_rate(list_of_bins):
    individual_rates = [sum(list_of_bins[i])/len(list_of_bins[i]) for i in range(len(list_of_bins))]
    return sum(individual_rates)/len(individual_rates), individual_rates
    
# my std error function to calculate standard errors from given list
def my_std_err(my_list):
    temp = 0
    average = sum(my_list)/len(my_list)
    for i in range(len(my_list)):
        temp = temp + math.pow((my_list[i]-average), 2)
    std_dev = math.sqrt(temp)/math.sqrt(len(my_list)-1)
    std_err = std_dev/math.sqrt(len(my_list))
    return std_err

############################################### extracting data and calculations    
    
# read all csv files from the folder in the given path=get data in the form of list of lists
# each list contains all timestamps from a single csv file
my_data = read_all(src)
start, end = get_border_times(my_data)     # get first and last common date from all data
common_data = extract_times(my_data, start, end)   # extract only common dates from all data to plot
nights = get_intervals(common_data[0], lights_out, lights_on, start, end)   # get nighttime intervals
days = reverse_intervals(start, end, nights)  #daytime intervals
full_nights_only = get_12h_intervals(nights)    # list of tuples of start and end time of each night interval)
full_days_only = get_12h_intervals(days)        # list of tuples of start and end time of each day interval)
common_days_nights = get_days_and_nights(common_data, full_nights_only, full_days_only) # equal number of days and nights

############################### print the analyzis in the console

night_rate, night_error, night2ttest = get_nights_rate(common_days_nights, full_nights_only)
print "Pellets per hour by night: ", night_rate, "err: ", night_error
day_rate, day_error, day2ttest = get_nights_rate(common_days_nights, full_days_only)
print "Pellets per hour by night: ", day_rate,"err: ", day_error

# ttest
ttest, p = ttest_ind(night2ttest, day2ttest)
print "p = ", p

############################################################## plot

N = 2       # number of bars to plot(dark and light) 
fig = plt.figure(facecolor='w') 
x = np.arange(N)    # arrange columns

ax1 = plt.subplot2grid((1,1),(0,0))
plt.ylabel('Eating rate (pellets/hour)')
ax1.set_frame_on(False)
y = [night_rate, day_rate]
# yerr first in tuple is to first colunm second to second, 
# first tuple is for positive values, second for negative
# drk, lght = plt.bar(x, y, width = 0.7, yerr=[(10,2),(10,2)])
drk, lght = plt.bar(x, y, width = 0.7, yerr=[(night_error,day_error),(night_error,day_error)], ecolor='k')
centers = x + 0.5*drk.get_width()     # align labels in the center
ax1.set_xticks(centers)
drk.set_facecolor('0.85')   # shade of gray
lght.set_facecolor('w')
ax1.set_xticklabels(['Dark', 'Light'])

# check p < 0.01(**), p < 0.05(*)
if p < 0.05:
    text = '*' if p >= 0.01 else '**'
    a = (centers[0] + centers[1])/2
    b = 1.05*max(y[0],y[1])
    dx = abs(centers[0]-centers[1])
    props = {'connectionstyle':'bar','arrowstyle':'-',\
                 'shrinkA':20,'shrinkB':20,'lw':1}
    # position the text in the middle on the top of the bar
    ax1.annotate(text, xy=(centers[0]+(dx/2.2),1.5*b), zorder=10)
    ax1.annotate('', xy=(centers[0],b), xytext=(centers[1],b), arrowprops=props)
    plt.ylim(ymax=b+(0.6*b))

plt.show()
