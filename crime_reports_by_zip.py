'''
This code takes the data set reporting crime for different zip codes. It gets the count of the total number of crime activities
reported for each zip code and then coming up with a score for each zip code.

A score between 1 to 5 is assigned to each zip-code depending on the corrsponding count value. A score of 1 is assigned to the zip codes having the most number of
complaints and 5 for the ones that recieve the least.

The output of this code is a dictionary having key as the zip code and corresponding value as the rank.
'''


import csv
from collections import defaultdict
import re
import os
import urllib2


zip_count=defaultdict(int)
surveyData = csv.reader(open("last_crime_nyc.csv"), delimiter=",")

for row in surveyData:
	if row[8] != '':
		zip_count[row[8]] +=1

	

#print zip_count  

sorted_count=sorted(zip_count,key=zip_count.get,reverse=True) 

list_len=len(zip_count)
#print list_len


for i in range(0,list_len):
	rslt=sorted_count[i]
	
	if zip_count[rslt] < 100:
		zip_count[rslt]=5
	
	if (zip_count[rslt] >= 100 and zip_count[rslt] < 500):
		zip_count[rslt]=4
	
	if (zip_count[rslt] >= 500 and zip_count[rslt] < 1000):
		zip_count[rslt]=3
	
	if (zip_count[rslt] >= 1000 and zip_count[rslt] < 2000):
		zip_count[rslt]=2
	
	if (zip_count[rslt] >= 2000):
		zip_count[rslt]=1
	
	print "%r,%r" %(rslt,zip_count[str(rslt)])	
		
