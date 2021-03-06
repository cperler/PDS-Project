'''
This code takes the data sets reporting noise complaints for different zip codes. It get the count of the total number of noise complaints
reported for each zip code and then coming up with a score for each zip code.

A score between 1 to 5 is assigned to each zip-code depending on the corrsponding count value. A score of 1 is assigned to the zip codes having the most number of
complaints and 5 for the ones that recieve the least.

The output of this code is a dictionary having key as the zip code and corresponding value as the safety score.
'''


import csv
from collections import defaultdict
import re
import os
import urllib2

#u = urllib2.urlopen('https://data.cityofnewyork.us/api/views/yts9-kmw9/rows.json?accessType=DOWNLOAD')
surveyData = csv.reader(open("Night_Noise_Survey_Manhattan.csv"), delimiter=",")
surveyData2 = csv.reader(open("Noise_Complaints.csv"), delimiter=",")
surveyData3 = csv.reader(open("Noise.csv"), delimiter=",")
surveyData4 = csv.reader(open("DATA_MAP_NOISE_1.csv"), delimiter=",")
surveyData5 = csv.reader(open("311_Noise_in_NYC.csv"), delimiter=",")
surveyData6 = csv.reader(open("Commercial_Noise.csv"), delimiter=",")

zip_count=defaultdict(int)

for row in surveyData:
    zip_count[row[8]] +=1

for row in surveyData2:
    zip_count[row[8]] +=1

for row in surveyData3:
    zip_count[row[8]] +=1

for row in surveyData4:
    zip_count[row[8]] +=1

for row in surveyData5:
    zip_count[row[8]] +=1	

for row in surveyData6:
    zip_count[row[8]] +=1		
            
print zip_count        

sorted_count=sorted(zip_count,key=zip_count.get,reverse=True) 

list_len=len(zip_count)
print list_len

#print sorted_count
diff= int(zip_count[sorted_count[0]])


for i in range(0,list_len):
	rslt=sorted_count[i]
	if zip_count[rslt] < diff/5:
		zip_count[rslt]=5
	
	if (zip_count[rslt] >= diff/5 and zip_count[rslt] < 2* diff/5):
		zip_count[rslt]=4
	
	if (zip_count[rslt] >= 2* diff/5 and zip_count[rslt] < 3* diff/5):
		zip_count[rslt]=3
	
	if (zip_count[rslt] >= 3* diff/5 and zip_count[rslt] < 4* diff/5):
		zip_count[rslt]=2
	
	if (zip_count[rslt] >= 4* diff/5):
		zip_count[rslt]=1
	
	print "% r,% r   " %(rslt,zip_count[str(rslt)])
		
