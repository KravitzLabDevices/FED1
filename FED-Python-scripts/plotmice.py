'''
Author: kravitzlab, based on matlab code by Katrina Nguyen
Date: May 27 2016
Purpose: to create an open source python code that plots Fig.2.(D) from 
Nguyen et al. Journal of Neuroscience Methods 267 (2016) 108-114.
for different data.
'''

'''
Description: The application reads the data from all csv files that
appear in the given folder. It assumes the first column in the csv files
are timestamps in the format: %m/%d/%Y %H:%M:%S (this is how the file from 
FED's SD card looks like). The folder selection, time bin size and nighttime hours
can be chosen through the GUI. Based on the given data, the application will:
Draw pellet retrieval events by individual mouse(upper plot). Separate row for each mouse.
Starts plotting from the bottom.
Shade area representing given nighttimes.
Plot average pellet retrieval by all mice in the given time intervals(lower plot).
Shade standard error for the plot.

'''

'''
Requirements: Anaconda(Python3.5)
Tested on Windows7.
'''

import os, sys
import tkinter
from tkinter import *
from tkinter import filedialog
import fnmatch
import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib.cm as cm
import datetime as dt
from datetime import timedelta
import time
import numpy as np
import math
import csv


# default application variables in the initial options window  
fields = ['Time bin in seconds', 'Lights out hour', 'Lights on hour']     
variables = ['1800','15','3']   # 30min interval in seconds(1800sec), lights out at 3pm, lights on at 3am

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
    if bin < 60 or bin > 7200 or lights_out < 0 or lights_out >= 24 or lights_on < 0 or lights_on >= 24:
        popup_msg("Time bin has to be 60-7200sec\nHours in 24hour format")
except:
    popup_msg("Wrong input")

# display folders through Tkinter, tkFileDialog
# set the path to the folder according to users choice
src = filedialog.askdirectory()
    
x_tick_hours = 0 # hour displayed on the X axis(24hours format)

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
        for line in the_data: 
            try:
                if int(line[1]) != 0:                     
                    my_cols.append(md.num2date(convertTime(line[0]), tz=None))
            except:
                continue    
    return my_cols

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
        popup_msg("No file was read")
    else:
        for i in range(len(list_all)):
            if len(list_all[i]) == 0:
                popup_msg("Some files were not read")
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
# end_hour=end of inghttime(24hours:1-00), and start and end time of a whole plot(data from: get_border_times(list_all))
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
# function to find number of bins given 2 times and a desired time interval  
# time difference is a timedelta type, it is first converted to seconds and divided by interval in seconds 
def get_number_of_bins (latest, earliest, tinterval):
    return int(math.floor((latest-earliest).total_seconds()/tinterval))

# fill each bin(number of bins=number of time intervals) according to the data from each file 
# returns list of lists of bins (number of lists=number of files)  
# takes as arguments number of all intervals(bins calculated from get_number_of_bins function), 
# list of lists of timestamps (result of extract_times function), earliest common date, and time interval(e.g. 30min=1800sec) in seconds  
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
 
# return list of sums from all mice for each time interval(helper function)
# takes as an argument list of lists(result of fill_bins function), and number of intervals(from get_number_of_bins function)
def get_sums(all_bin_lists, intervalsNo):
    # store the sums in the list
    interval_sums = np.zeros(intervalsNo)
    for i in range(len(all_bin_lists)):
        for j in range(intervalsNo):
            interval_sums[j] += all_bin_lists[i][j]
    return interval_sums
    
# return list of averages to plot
# takes as an argument list of lists(result of fill_bins function), and number of intervals(from get_number_of_bins function)
def get_averages2plot(all_bin_lists, intervalsNo):
    interval_sum = get_sums(all_bin_lists, intervalsNo)
    # create a list of averages 
    interval_averages = [float(interval_sum[i])/len(all_bin_lists) for i in range(intervalsNo)]
    return interval_averages

# return standard error
def get_std_err(all_bin_lists):
    interval_elements = list()    
    for i in range(len(all_bin_lists[0])):
        temp_el = list()
        for j in range(len(all_bin_lists)):
            temp_el.append(all_bin_lists[j][i])
        interval_elements.append(temp_el)
    # calculate standard deviation and divide it by square root of total number of files
    # note: np.std calculates biased sample standard deviation estimator (divides by N), temp introduces Bessel's correction 
    # (divides by N-1) yielding unbiased stdev estimator (important for small samples size)
    try:
        temp = math.sqrt(len(all_bin_lists))/math.sqrt(len(all_bin_lists)-1)
        std_err = [float(np.std(interval_elements[i])*temp)/math.sqrt(len(all_bin_lists)) for i in range(len(all_bin_lists[0]))]
    except:
        std_err = -1
    return std_err
    
# make an array of times to plot(for Xaxis values)
def times_intervals_for_avg(intervalsNo, earliest, interval):
    times = list()
    for i in range(intervalsNo):
        times.append(earliest + dt.timedelta(seconds=(interval * i)))
    return times
    
############################# extracting data and calculations 
 
# read all csv files from the folder in the given path=get data in the form of list of lists
# each list contains all timestamps from a single csv file
data = read_all(src)
start, end = get_border_times(data)     # get first and last common date from all data
plot_data = extract_times(data, start, end)   # extract only common dates from all data to plot
nights = get_intervals(plot_data[0], lights_out, lights_on, start, end)   # get nighttime intervals to plot shades later
how_many_bins = get_number_of_bins(end, start, bin)     # count how many bins will there be for the given data
all_bin_counts = fill_bins(how_many_bins, plot_data, start, bin)
avg = get_averages2plot(all_bin_counts, how_many_bins)  # get average number of timstamps (pellet retrieval)
avg_times = times_intervals_for_avg(how_many_bins, start, bin)  # timeline for Xaxis to plot avg
std_err = get_std_err(all_bin_counts)       # calculate standard error
# get data to plot standard error around average plot
if std_err != -1:
    positive_std_err_plot = [avg[i]+std_err[i] for i in range(len(std_err))]
    negative_std_err_plot = [avg[i]-std_err[i] for i in range(len(std_err))]

################################## ploting

fig = plt.figure(facecolor='w') 
ax1 = plt.subplot2grid((2,1),(0,0))
plt.title('Pellet retrieval events by individual mice')
ax1.set_frame_on(False)
ax1.axes.get_yaxis().set_visible(False)
ax1.axes.get_xaxis().set_visible(False)
# for each file, plot timestamps(events) in the same order as 
# the files were read from the folder (starts at the bottom)
# take  row colors from the colormap(cm.prism)
# more colormaps on: http://scipy.github.io/old-wiki/pages/Cookbook/Matplotlib/Show_colormaps
color_distancer = 5    ## in order to distance the colors from eachother (i is to small to see the difference)
# plot each data in a separate row in different color 
for i in range(len(plot_data)):   
    ax1.eventplot(plot_data[i], colors= [cm.prism(color_distancer)], lineoffsets=i+1, linelengths=1)
    color_distancer += 15    
# shade night intervals
for interval in nights:
    t0, t1 = interval
    ax1.axvspan(t0, t1, alpha=0.2, facecolor='gray')  
    
ax1 = plt.gca()  # get the current axes
# format of date displayed on the x axis
xfmt = md.DateFormatter('%H:%M\n%m-%d-%y')
ax1.xaxis.set_major_formatter(xfmt)
# what hour ticks will be vivible (byhour)
major_hour = md.HourLocator(byhour=x_tick_hours, interval=1)
ax1.xaxis.set_major_locator(major_hour)

# add second subplot to plot average intake(shares the same Xaxis timeline)
ax2 = plt.subplot2grid((2,1),(1,0), sharex=ax1)
plt.ylabel('Average pellet retrieval')
# plot averages and standard error
ax2.plot(avg_times, avg, color='k', linewidth=2.0)
if std_err != -1:
    ax2.fill_between(avg_times, positive_std_err_plot, negative_std_err_plot, 
                    alpha=0.2, facecolor='gray', edgecolor="gray", linewidth=0.0, 
                    hatch='|||', label = 'Standard error') 
else:
    popup = Tk()
    popup.wm_title("!")
    label = Label(popup, text="Not enough data to calculate\nstandard error!\n\nPress 'ok' in Options window again\nto see the plot anyway.")
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Ok", command = lambda: popup.withdraw())
    B1.pack()
    popup.mainloop()
# shade night intervals
for interval in nights:
    t0, t1 = interval
    ax2.axvspan(t0, t1, alpha=0.2, facecolor='gray')  
 
# adjust positions between subplots
plt.subplots_adjust(left=0.11, bottom=0.11, right=0.90, top=0.90, wspace=0, hspace=0)
if std_err != -1:
    plt.legend() 
plt.show()


# Links to eventplot docs:
# http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.eventplot
# http://matplotlib.org/examples/pylab_examples/eventplot_demo.html
# About user input entries in tkinter
# http://www.python-course.eu/tkinter_entry_widgets.php

    
