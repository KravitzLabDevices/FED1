'''
Author: Ilona Szczot
Date: July 15 2016
Purpose: The application processes multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse. It extracts only common full 12 hours daytime and nighttime intervals, in order
to later compare data sets from equal sized nighttime and daytime periods. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time intervals between
pellets retrieved separating meals(for example if a mouse retrieved last pellet more than 30 min ago,
the next pellet retrieved after that period, will not be considered the same meal). User can also specify
what size in grams is a meal, and what size of pellets(in grams) was used during the experiment.
Then, according to the given parameters, the application plots four bar charts with the results
of analyzis and standard errors. Top left = "Pellets in meals" (total pellets retrieved during meals by average mouse). 
Top right = "Meal duration(min)". Bottom left = "Pellets eaten during meals(%)". Bottom right = "Meals per cycle".
In addition, the program prints out the values in the console.
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
    # check how many dates(calendar days) are in the file
    for el in list_of_timestamps:
        if el.date() not in dates_from_file:
            dates_from_file.append(el.date())
            
    # for each date in file create start_hour-end_hour pair of night interval (datetime, number format)
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

# returns a total pellets by given intervals, divided by number of interval
# to get a count per one night/day
def all_night_pellets(list_of_timestamps, intervals):
    total_count = list()
    for i in range(len(list_of_timestamps)):
        temp = 0
        for j in range(len(list_of_timestamps[i])):
            for val in intervals:
                start, end = val      #convert to date
                start = md.num2date(start)
                end = md.num2date(end)
                if list_of_timestamps[i][j] >= start and list_of_timestamps[i][j] <= end:
                    temp +=1
        total_count.append(temp)
    # count average from all mice and divide it by the number of nights
    return (sum(total_count)/len(total_count))/float(len(intervals))
    
# map meal size in grams to pellets number
# takes as arguments defined size of the meal in grams and pellet weight
# returns minimum number of pellets of defined size to be considered a meal according to the given meal size
def gram2pellet(grams, pellet):
	return math.ceil(grams/pellet)

# takes as an argument data(list of lists=e.g.8mice with list of timestamps for each one) 
# is a result of extract_times finction(common times for all mice). Second argument is a defined interval 
# for meal in seconds(e.g. 30 min=1800sec)
# returns a tuple of two lists(meals and durartions) that are candidates for meals and relevant time intervals
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
				if (el[i+1]-el[i]).total_seconds() <= interval: 		# if interval between the timestamps is less than e.g. 30 min, its a meal
					temp_meal.append(1)				# add one pellet to the meal candidate
					temp_interval.append(el[i])		# add a timestamp to temp interval
				else:		# if interval is greater than e.g. 30 min the i+1 will not be the same meal
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
# it takes as arguments the result of get_by_meal_interval function, and meal size in grams, and size of pellet in grams
# it returns a tuple, two lists one with proper meals and one with meal durations
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

# count pellets eaten during night meals, count time of night meals
# returns list of night meal sizes for each mouse and list of night meal durations
def night_count(total_meals, total_intervals, intervals):
    # e.g.8 lists of lists of night meal sizes(in pellets)/intervals of night meals
    night_meal_count = list()
    night_meal_duration = list()
    for i in range(len(total_intervals)):       # e.g.8 mice
        temp_m = list()
        temp_i = list()
        for j in range(len(total_intervals[i])):
            meal_start, meal_end = total_intervals[i][j][0],total_intervals[i][j][-1]
            for val in intervals:
                start, end = val  # it is in number format, needs to be converted to time
                start = md.num2date(start)
                end = md.num2date(end)
                if meal_start >= start and meal_start <= end:
                    temp_m.append(total_meals[i][j])
                    temp_i.append((meal_end - meal_start).total_seconds())
        if temp_m != 0:
            night_meal_count.append(temp_m)
            night_meal_duration.append(temp_i)
    return night_meal_count, night_meal_duration

# returns average of all night pellets retrieved during meals and average number of meals per cycle,
# and std error of meals
# it takes as argument meals list(first elemant of the result of night_count function), and nighttime/daytime intervals
def get_avg_night_pellets_per_meal(night_meal_count, intervals):
    # count sums(No of pellets per meal) for all mice indvivdually
    individual_meal_sums = list()    # list of 8 tuples: sum, len(number of meals)
    for el in night_meal_count:
        temp_sum = 0
        for i in range(len(el)):
            temp_sum += el[i]
        if temp_sum != 0:
            individual_meal_sums.append((temp_sum, len(el)))
            # print out the information
            print "sum of all meal pellets per mouse : number of meals", temp_sum, len(el)

    # count number of meals
    individual_mealNo = [individual_meal_sums[i][1] for i in range(len(individual_meal_sums))]
    avg_mealNo_in_cycle = float(sum(individual_mealNo)/len(individual_mealNo))/len(intervals) if len(individual_mealNo) != 0 else 0
    
    # count std error
    data2err = [individual_mealNo[i]/len(intervals) for i in range(len(individual_mealNo))]   
    err_meals = my_std_err(data2err)

    # count individual avg
    # try to avoid division by 0, when no pellets were retrieved as meals
    individual_avg = list()
    for i in range(len(individual_meal_sums)):
        if individual_meal_sums[i][1] == 0:     # if there were no meals
            pass
        else:
            individual_avg.append(individual_meal_sums[i][0]/individual_meal_sums[i][1])
    # count average from all averages
    pellet_avg = float(sum(individual_avg))/len(individual_avg) if len(individual_avg) != 0 else 0
    return pellet_avg, avg_mealNo_in_cycle, err_meals, data2err

# how many total pellets on average during night meals were retrieved,
# divide it by the number of nights to have the result per one cycle
def all_night_meal_pellets_count(night_meal_count, intervals):
    # count sums for all mice indvivdually
    individual_meal_sums = list()    
    for el in night_meal_count:
        temp_sum = 0
        for i in range(len(el)):
            temp_sum += el[i]
        if temp_sum != 0:
            individual_meal_sums.append(temp_sum)

    # count std error
    data2err = [float(sum(night_meal_count[i]))/len(intervals) for i in range(len(night_meal_count))]
    error = my_std_err(data2err)
    count = (sum(individual_meal_sums)/len(individual_meal_sums)) if len(individual_meal_sums) != 0 else 0
    return count/float(len(intervals)), error, data2err

# returns average meal duration(according to the given list: either nighttime, or daytime), and std err
def get_avg_night_meal_duration(night_meal_duration):   
    # count interval sums for all mice individually
    individual_interval_sums = list()
    for el in night_meal_duration:
        temp_sum = 0
        for i in range(len(el)):
            temp_sum += el[i]
        if temp_sum != 0:
            individual_interval_sums.append((temp_sum, len(el)))
    
    # count individual avg
    individual_time_avg = list()
    for i in range(len(individual_interval_sums)):
        if individual_interval_sums[i][1] == 0:
            pass
        else:
            individual_time_avg.append(individual_interval_sums[i][0]/individual_interval_sums[i][1])

    # count std err
    data2err = [float(individual_time_avg[i]/60) for i in range(len(individual_time_avg))]
    std_err_dur = my_std_err(data2err)
    
    # count average from all averages
    duration_avg = float(sum(individual_time_avg))/len(individual_interval_sums) if len(individual_interval_sums) != 0 else 0
    # return duration in minutes (divide seconds/60)
    return round(duration_avg/60), std_err_dur, data2err

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
full_nights = get_12h_intervals(nights)
full_days = get_12h_intervals(days)
data2plot = get_days_and_nights(common_data, full_nights, full_days)

meals, durations = get_by_meal_size(get_by_meal_interval(data2plot, meal_interval), meal_size, pellet_weight)

############################### print the analyzis in the console
# get data for night stats
print
print "Night"
print "-----"
total_night_count, total_night_durations = night_count(meals, durations, full_nights)
night_avg_pellet_per_meal, mealNo_night, mealNo_err_night, mealNo_night2test = get_avg_night_pellets_per_meal(total_night_count, full_nights)
print "Night average pellets per meal, avg meals per cycle", night_avg_pellet_per_meal, mealNo_night, "err",mealNo_err_night
night_avg_meal_duration, duration_err_night, night_avg_meal_duration_p = get_avg_night_meal_duration(total_night_durations)
print "Night average meal duration in min", night_avg_meal_duration, "err",duration_err_night
night_meal_pellet_count, meal_count_err_night, night_meal_pelet_count2test = all_night_meal_pellets_count(total_night_count, full_nights)
print "Total pellets retrieved during single night meals by average mouse", night_meal_pellet_count, "err",meal_count_err_night 
total_night_pellets = all_night_pellets(data2plot, full_nights)
print "All single night pellets", total_night_pellets
prctg_night = night_meal_pellet_count*100/float(total_night_pellets)
prctg_night_err = meal_count_err_night*100/total_night_pellets
print "%Pellets during night meals", prctg_night, "err",prctg_night_err
print "------------------------------------------------------------"
print
# get data for day stats
print "Day"
print "---"
total_day_count, total_day_durations = night_count(meals, durations, full_days)
day_avg_pellet_per_meal, mealNo_day, mealNo_err_day, mealNo_day2test  = get_avg_night_pellets_per_meal(total_day_count, full_days)
print "Day average pellets per meal, avg meals per cycle", day_avg_pellet_per_meal, mealNo_day,"err",mealNo_err_day
day_avg_meal_duration, duration_err_day, day_avg_meal_duration_p = get_avg_night_meal_duration(total_day_durations)
print "Day average meal duration in min", day_avg_meal_duration, "err", duration_err_day
day_meal_pellet_count, meal_count_err_day, day_meal_pelet_count2test = all_night_meal_pellets_count(total_day_count, full_days)
print "Total pellets retrieved during single day meals by average mouse", day_meal_pellet_count, "err",meal_count_err_day
total_day_pellets = all_night_pellets(data2plot, full_days)
print "All single day pellets", total_day_pellets
prctg_day = day_meal_pellet_count*100/float(total_day_pellets)
prctg_day_err = meal_count_err_day*100/total_day_pellets
print "%Pellets during night meals", prctg_day, "err", prctg_day_err


# ttest
top_left_ttest, top_left_p = ttest_ind(night_meal_pelet_count2test, day_meal_pelet_count2test)
print "Pellets in meals p = ", top_left_p
top_right_ttest, top_right_p = ttest_ind(night_avg_meal_duration_p, day_avg_meal_duration_p)
print "Meal duration(min) p = ", top_right_p
# data to ttest for % pellets within meals
night_meal2total2ttest = []
for el in night_meal_pelet_count2test:
    night_meal2total2ttest.append(el/float(total_night_pellets))
day_meal2total2ttest = []
for el in day_meal_pelet_count2test:
    day_meal2total2ttest.append(el/float(total_day_pellets))
bottom_left_ttest, bottom_left_p = ttest_ind(night_meal2total2ttest, day_meal2total2ttest)
print "Pellets during night meals(%) p = ", bottom_left_p
bottom_right_ttest, bottom_right_p = ttest_ind(mealNo_night2test, mealNo_day2test)
print "Meals per cycle p = ", bottom_right_p


############################################################# plot

N = 2       # number of bars to plot(dark and light) 
fig = plt.figure(facecolor='w') 
x = np.arange(N)    # arrange columns

############ first subplot(top left), "Pellets in meals"
ax1 = plt.subplot2grid((2,2),(0,0))
plt.ylabel('Pellets in meals')
ax1.set_frame_on(False)
y = [night_meal_pellet_count, day_meal_pellet_count]
# yerr first in tuple is to first colunm second to second, 
# first tuple is for positive values, second for negative
# drk, lght = plt.bar(x, y, width = 0.7, yerr=[(10,2),(10,2)])
drk, lght = plt.bar(x, y, width = 0.7, yerr=[(meal_count_err_night,meal_count_err_day),(meal_count_err_night,meal_count_err_day)], ecolor='k')
centers = x + 0.5*drk.get_width()     # align labels in the center
ax1.set_xticks(centers)
drk.set_facecolor('0.85')   # shade of gray
lght.set_facecolor('w')
ax1.set_xticklabels(['Dark', 'Light'])

# check p < 0.01(**), p < 0.05(*)
if top_left_p < 0.05:
    text = '*' if top_left_p >= 0.01 else '**'
    a = (centers[0] + centers[1])/2
    b = 1.05*max(y[0],y[1])
    dx = abs(centers[0]-centers[1])
    props = {'connectionstyle':'bar','arrowstyle':'-',\
                 'shrinkA':20,'shrinkB':20,'lw':1}
    # position the text in the middle on the top of the bar
    ax1.annotate(text, xy=(centers[0]+(dx/2.2),1.5*b), zorder=10)
    ax1.annotate('', xy=(centers[0],b), xytext=(centers[1],b), arrowprops=props)
    plt.ylim(ymax=b+(0.6*b))


############### second subplot(top right), "Meal duration(min)"
ax2 = plt.subplot2grid((2,2),(0,1))
plt.ylabel('Meal duration(min)')
ax2.set_frame_on(False)
y = [night_avg_meal_duration, day_avg_meal_duration]
drk, lght = plt.bar(x, y, width = 0.7, yerr=[(duration_err_night,duration_err_day),(duration_err_night,duration_err_day)], ecolor='k')
centers = x + 0.5*drk.get_width()     # align labels in the center
ax2.set_xticks(centers)
drk.set_facecolor('0.85')   # shade of gray
lght.set_facecolor('w')
ax2.set_xticklabels(['Dark', 'Light'])

# check p < 0.01(**), p < 0.05(*)
if top_right_p < 0.05:
    text = '*' if top_right_p >= 0.01 else '**'
    a = (centers[0] + centers[1])/2
    b = 1.1*max(y[0],y[1])
    dx = abs(centers[0]-centers[1])
    props = {'connectionstyle':'bar','arrowstyle':'-',\
                 'shrinkA':20,'shrinkB':20,'lw':1}
    # position the text in the middle on the top of the bar
    ax2.annotate(text, xy=(centers[0]+(dx/2.2),1.5*b), zorder=10)
    ax2.annotate('', xy=(centers[0],b), xytext=(centers[1],b), arrowprops=props)
    plt.ylim(ymax=b+(0.6*b))


############ third subplot(bottom left), "Pellets eaten during meals(%)"
ax3 = plt.subplot2grid((2,2),(1,0))
plt.ylabel('Pellets eaten during meals(%)')
ax3.set_frame_on(False)
y = [prctg_night, prctg_day]
drk, lght = plt.bar(x, y, width = 0.7, yerr=[(prctg_night_err,prctg_day_err),(prctg_night_err,prctg_day_err)], ecolor='k')
centers = x + 0.5*drk.get_width()     # align labels in the center
ax3.set_xticks(centers)
drk.set_facecolor('0.85')   # shade of gray
lght.set_facecolor('w')
ax3.set_xticklabels(['Dark', 'Light'])

# check p < 0.01(**), p < 0.05(*)
if bottom_left_p < 0.05:
    text = '*' if bottom_left_p >= 0.01 else '**'
    a = (centers[0] + centers[1])/2
    b = 1.1*max(y[0],y[1])
    dx = abs(centers[0]-centers[1])
    props = {'connectionstyle':'bar','arrowstyle':'-',\
                 'shrinkA':20,'shrinkB':20,'lw':1}
    # position the text in the middle on the top of the bar
    ax3.annotate(text, xy=(centers[0]+(dx/2.2),1.5*b), zorder=10)
    ax3.annotate('', xy=(centers[0],b), xytext=(centers[1],b), arrowprops=props)
    plt.ylim(ymax=b+(0.6*b))


############ fourth subplot(bottom right), "Meals per cycle"
ax4 = plt.subplot2grid((2,2),(1,1))
plt.ylabel('Meals per cycle')
ax4.set_frame_on(False)
y = [mealNo_night, mealNo_day]
drk, lght = plt.bar(x, y, width = 0.7, yerr=[(mealNo_err_night,mealNo_err_day),(mealNo_err_night,mealNo_err_day)], ecolor='k')
centers = x + 0.5*drk.get_width()     # align labels in the center
ax4.set_xticks(centers)
drk.set_facecolor('0.85')   # shade of gray
lght.set_facecolor('w')
ax4.set_xticklabels(['Dark', 'Light'])

# check p < 0.01(**), p < 0.05(*)
if bottom_right_p < 0.05:
    text = '*' if bottom_right_p >= 0.01 else '**'
    a = (centers[0] + centers[1])/2
    b = 1.1*max(y[0],y[1])
    dx = abs(centers[0]-centers[1])
    props = {'connectionstyle':'bar','arrowstyle':'-',\
                 'shrinkA':20,'shrinkB':20,'lw':1}
    # position the text in the middle on the top of the bar
    ax4.annotate(text, xy=(centers[0]+(dx/2.2),1.5*b), zorder=10)
    ax4.annotate('', xy=(centers[0],b), xytext=(centers[1],b), arrowprops=props)
    plt.ylim(ymax=b+(0.6*b))

# adjust positions between subplots
plt.subplots_adjust(left=0.11, bottom=0.11, right=0.90, top=0.90, wspace=0.3, hspace=0.3)

plt.show()














