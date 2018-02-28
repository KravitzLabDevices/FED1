This page references FED1.0, published by Nguyen et al: 
https://www.ncbi.nlm.nih.gov/pubmed/27060385

FED2.0 will be released shortly. This new version is easier to build, cheaper, and more reliable.  If you are new to FED please hold off on buildling FED1 and check this page in the next few weeks for an updated build.  If you want to check in on the status of FED2.0, please <a href="mailto:lex.kravitz@nih.gov"> send us an email. </a>.  Thanks!

# Feeding Experimentation Device (FED)
## What is it?
<img src="https://github.com/KravitzLab/FED/blob/master/doc/photos/FED%20front3.jpg" height="200">
<img src="https://github.com/KravitzLab/FED/blob/master/doc/FED%20gif%202.gif" height="200">
<img src="https://github.com/KravitzLab/FED/blob/master/doc/FED%20gif%203.gif" height="200">  
Feeding Experimentation Device (FED) is a free, open-source system for measuring feeding in rodents. FED uses an Arduino processor, 
stepper motor, infrared beam detector, and SD card to provide feeding records of pellets eaten by singly housed rodents. FED runs off of a battery, which allows it to be placed in colony caging or within other experimental equipment. The electronics for building each FED cost around $150USD, and the 3d printed parts cost between $20 and $400, depending on access to 3D printers and desired print quality. 

FED is open-source - we encourage you to fork, modify, and hack it to add new functionality. We'd also love to hear about it when you do, so please <a href="mailto:lex.kravitz@nih.gov">drop us a line</a>!

## What's available?
+ <b> FED-wiki </b>  
If you'd like to build your own FED, head to the wiki for detailed build instructions: https://github.com/KravitzLab/fed/wiki/

Other links above:

+ <b>3D_Printing_Files</b>  
STL files for 3D printing 
(please contact us if any other file formats are needed)

+ <b>FED-Python-scripts</b>  
Analysis code written in Python

+ <b>doc</b>  
Documentation and photos

+ <b>FED-arduino</b>  
The latest Arduino sketch for running FED. We've recently added a new version to the Arduino code (FED_SD_VersionB) to account for Adafruit's newely released SD shield. In order to find out whether you have SD shield version A or B, please go to the following URL: https://learn.adafruit.com/adafruit-data-logger-shield/wiring-and-config 

+ Note: once coin battery is inserted into the SD shield, please don't remove it! This prevents Real Time Clock (RTC) errors.

+ <b>hardware</b>  
System schematic

FED was designed by a team of researchers at the National Institutes of Health, more info here: http://www.kravitzlab.com/


