'''
Author: kravitzlab
Date: June 23 2016
Purpose: given multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse, the application plots rows of timestamps separate for each file(mouse).
Application extracts only common full 12 hours daytime and nighttime intervals. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time intervals between
pellets retrieved separating meals(for example if a mouse retrieved last pellet more than 30 min ago,
the next pellet retrieved after that period, will not be considered the same meal). User can also specify
what size in grams is a meal, and what size of pellets(in grams) was used during the experiment.
Then, according to the given parameters, the application plots lines connecting timestamps that are considered 
a meal. Each horizontal line is a meal, each vertical line is a timestamp.
'''

'''
Requirements: Anaconda(Python3.5)
Tested on Windows7.
'''

import os, sys
import fnmatch
import tkinter
from tkinter import *
from tkinter import filedialog
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
fields = ['Lights out hour', 'Lights on hour', 'Time between meals in sec', 'Meal in grams', 'Pellet in grams']     
variables = ['15','3', '1800', '0.3', '0.02']   # lights out at 3pm, lights on at 3am, 30 min intervals, meal>=0.3g, pellet=0.02g

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
        lab = Label(row, width=25, text=fields[i], anchor='w')
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
	lights_out = int(variables[0])     
	lights_on = int(variables[1])   
	meal_interval = int(variables[2])	
	meal_size = float(variables[3])		
	pellet_weight = float(variables[4])
	if lights_out <= 0 or lights_out >= 24 or lights_on <= 0 or lights_on >= 24:
		popup_msg("Hours in 24hour format")
	elif meal_interval < 60 or meal_interval > 7400 or meal_size < 0.1 or meal_size > 1 or pellet_weight < 0.01 or pellet_weight > 1:
		popup_msg("Meal intervals between 60-7400sec\nMeal and pellets between 0.1-1g")
except:
	popup_msg("Wrong input")

# display folders through Tkinter, tkFileDialog
# set the path to the folder according to users choice
src = filedialog.askdirectory()

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

# returns daytime intervals based on nights   
def reverse_intervals(earliest, latest, interval):
    daytime = list()
    earliest = md.date2num(earliest)      # beginning of plot      
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
# given list of intervals as parameter it returns only the ones that last full 12 hours
def get_12h_intervals(interval):
    my_intervals = list()
    for el in interval:
        # convert time number to date in order to compare, 43200sec=12hours
        if (md.num2date(el[1]) - md.num2date(el[0])).total_seconds() == 43200:
            my_intervals.append(el)
    return my_intervals

# returns full 12hour nights and days(all timestamps), where number of days = number of nights
# takes as an argument list of all timestamps, list of nighttime intervals and a list of daytime intervals
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

# map meal size in grams to pellets number
# takes as arguments defined size of the meal in grams and pellet weight
# returns minimum number of pellets of defined size to be considered a meal according to the given meal size
def gram2pellet(grams, pellet):
	return math.ceil(grams/pellet)

# takes as an argument data(list of lists=e.g.8mice with list of timestamps for each one) 
# a result of get_days_and_nights. Second argument is a defined interval 
# for meal in seconds(e.g. 30 min=1800sec)
# returns a tuple of two lists that are candidates for meals and relevant time intervals
def get_by_meal_interval(data, interval):
	# initial all meals without checking the grams of meals
	init_meals = []
	# initial all time intervals for the above candidate meals
	init_intervals = []
	# for each of 8 mice
	for el in data:
		single_mouse_meals = []
		single_mouse_intervals = []
		temp_meal = []
		temp_interval = []
		for i in range(len(el)):	# for all timestamps in a mouse file
			if (i+1) < len(el):		# check if this is not the last timestamp
				if (el[i+1]-el[i]).total_seconds() <= interval: 		# if interval between the timestamps is less than e.g.30 min, its a meal
					temp_meal.append(1)				# add one pellet to the meal candidate
					temp_interval.append(el[i])		# add a timestamp to temp interval
				else:		# if interval is greater than e.g.30 min the i+1 will not be the same meal
					temp_meal.append(1)				# add the last pellet of the meal
					temp_interval.append(el[i])		# add the last timestamp to the meal
					single_mouse_meals.append(temp_meal)	# add a candidate meal to the single mouse meals
					single_mouse_intervals.append(temp_interval)
					temp_meal = []			# clear before the next meal
					temp_interval = []
			else:		# if it is the last timestamp
				temp_meal.append(1)				# add one pellet to the meal candidate
				temp_interval.append(el[i])		# add a timestamp to temp interval
				single_mouse_meals.append(temp_meal)	# add a candidate meal to the single mouse meals
				single_mouse_intervals.append(temp_interval)
		# end of iterating single mouse, so add data to common candidates		
		init_meals.append(single_mouse_meals)
		init_intervals.append(single_mouse_intervals)
	return init_meals, init_intervals

# function to extract a proper meal by the defined size of the meal
# it takes as an argument, the result of get_by_meal_interval function,
# defined size of a meal in grams, and defined size of a pellet
# it returns a tuple, two lists(one with meals, and one with relevant time intervals)
def get_by_meal_size(candidates, meal_grams, pellet_grams):
	init_meals, init_intervals = candidates
	extracted_meals = list()
	extracted_intervals = list()
	min_pellets = gram2pellet(meal_grams, pellet_grams)		# what is the min ammount of pellets for a meal
	for i in range(len(init_meals)):
		single_mouse_meals = []		# meals of each mouse
		single_mouse_intervals = []
		for j in range(len(init_meals[i])):
			meal = sum(init_meals[i][j])
			if meal >= min_pellets:
				single_mouse_meals.append(meal)
				single_mouse_intervals.append(init_intervals[i][j])
		extracted_meals.append(single_mouse_meals)		# add all mouse meals to extracted meals
		extracted_intervals.append(single_mouse_intervals)
	return extracted_meals, extracted_intervals

# create a dictionary with meal segments for each mouse to plot
def get_segments(time_intervals):
	segs = dict()
	for i in range(len(time_intervals)):
		segs[i+1] = []			# key starts with 1
		for j in range(len(time_intervals[i])):
			# add first and last timestamp of a meal that correspond to beginning and end of meal
			segs[i+1].append((time_intervals[i][j][0],time_intervals[i][j][-1]))
	return segs
    
############################# extracting data and calculations    
    
# read all csv files from the folder in the given path=get data in the form of list of lists
# each list contains all timestamps from a single csv file
my_data = read_all(src)
start, end = get_border_times(my_data)     # get first and last common date from all data
common_data = extract_times(my_data, start, end)   # extract only common dates from all data to plot
nights = get_intervals(common_data[0], lights_out, lights_on, start, end)   # get nighttime intervals
days = reverse_intervals(start, end, nights)  #daytime intervals
full_nights = get_12h_intervals(nights)         # get only 12 hour intervals
full_days = get_12h_intervals(days)
data2plot = get_days_and_nights(common_data, full_nights, full_days)    # get data with equal number of nights and days

# extract real meals and durations
meals, durations = get_by_meal_size(get_by_meal_interval(data2plot, meal_interval), meal_size, pellet_weight)

meal_time_segments = get_segments(durations)

############################## plot

fig = plt.figure(facecolor='w') 
ax1 = plt.subplot2grid((1,1),(0,0))

# for each file, plot timestamps(events) in the same order as 
# the files were read from the folder (starts at the bottom)
# take  row colors from the colormap(cm.prism)
# more colormaps on: http://scipy.github.io/old-wiki/pages/Cookbook/Matplotlib/Show_colormaps
color_distancer = 5    ## in order to distance the colors from eachother (i is to small to see the difference)
# plot each data in a separate row in different color 
for i in range(len(data2plot)):   
    ax1.eventplot(data2plot[i], colors= [cm.prism(color_distancer)], lineoffsets=i+1, linelengths=0.5)
    color_distancer += 15    
# shade night intervals
for interval in full_nights:
    t0, t1 = interval
    ax1.axvspan(t0, t1, alpha=0.2, facecolor='gray')  

ax1 = plt.gca()  # get the current axes
# format of date displayed on the x axis
xfmt = md.DateFormatter('%H:%M\n%m-%d-%y')
ax1.xaxis.set_major_formatter(xfmt)

# plot meal segments as lines connecting timestamps that are considered a meal
for i in meal_time_segments:
	for segment in meal_time_segments[i]:
		ax1.plot(segment, [i,i], color='k')

plt.show()
