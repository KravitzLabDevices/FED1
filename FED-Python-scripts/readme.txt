########################
# RUN THE APPLICATIONS #
########################

The easiest way to run all scripts is to install Anaconda platform: 
https://www.continuum.io/downloads
Make sure that python Anaconda version is either the only python version on your computer,
or set your python path to the Anaconda version instead.
Then you can run the script either by double clicking on the script file,
or in the cmd type: python <fileName.py>
or in the command line type: spyder 
to open interactive Python development environment, to access the source code.

All scripts accept csv files, where the first coulmn is a timestamp: %m/%d/%Y %H:%M:%S,
and second column is "Pellet Count". 
It is not necessary to remove headers in the FED's raw file, but it might be necessary to change
the first column's cell format in excel to "Custom", and save it as "Type": m/d/yyyy h:mm:ss,
before running the scripts.

------------------
Written and tested under Windows7
Anaconda(Python3.5)
------------------

plotmice.py
-----------
Purpose: The application reads the data from all csv files that
appear in the given folder. It assumes the first column in the csv files
are timestamps in the format: %m/%d/%Y %H:%M:%S (this is how the file from 
FED's SD card looks like). The folder selection, time bin size and nighttime hours
can be chosen through the GUI. Based on the given data, the application will:
1.Draw pellet retrieval events by individual mouse(upper plot). Separate row for each mouse.
Starts plotting from the bottom.
2.Shade area that represents given nighttimes.
3.Plot average pellet retrieval by all mice in the given time intervals(lower plot).
4.Shade standard error for the plot.
------------------------------------


meals.py
--------
Purpose: given multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse, the application plots rows of timestamps separate for each file(mouse).
Application extracts only common full 12 hours daytime and nighttime intervals. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time intervals between
pellets retrieved separating meals(for example if a mouse retrieved last pellet more than 30 min ago,
the next pellet retrieved after that period, will not be considered the same meal). User can also specify
what size in grams is a meal, and what size of pellets(in grams) was used during the experiment.
Then, according to the given parameters, the application plots lines connecting timestamps that are considered 
a meal. Each horizontal line is a meal, each vertical line is a timestamp.
--------------------------------------------------------------------------

meal_bars.py
------------
Purpose: The application processes multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse. It extracts only common full 12 hours daytime and nighttime intervals, in order
to later compare data sets from equal sized nighttime and daytime periods. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time intervals between
pellets retrieved separating meals(for example if a mouse retrieved last pellet more than 30 min ago,
the next pellet retrieved after that period, will not be considered the same meal). User can also specify
what size in grams is a meal, and what size of pellets(in grams) was used during the experiment.
Then, according to the given parameters, the application plots four bar charts with the results
of analyzis and standard errors, and a statistical significance(ttest), if there is one('*' for p < 0.05, '**' for p < 0.01). 
Top left = "Pellets in meals" (total pellets retrieved during meals by average mouse). Top right = "Meal duration(min)". 
Bottom left = "Pellets eaten during meals(%)". Bottom right = "Meals per cycle".
In addition, the program prints out the values in the console.
--------------------------------------------------------------

eating_rate.py
--------------
Purpose: The application processes multiple files with timestamps(first column of a csv file) corresponding to the
single pellet retrieved by a mouse. It extracts only common full 12 hours daytime and nighttime intervals, in order
to later compare data sets from equal sized nighttime and daytime periods. User can define what were
the nighttime and daytime hours in the experiment. User can also define the time for calculating the eating rate
(between pellets per 1 min and per 2 hours).Then, according to the given parameters, the application plots a bar chart
with the results of the analyzis, and standard errors, and a statistical significance(ttest), if there is one
('*' for p < 0.05, '**' for p < 0.01). In addition, the program prints out the values in the console.
-----------------------------------------------------------------------------------------------------
