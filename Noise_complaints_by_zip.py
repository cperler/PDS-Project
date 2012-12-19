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


def get_noise_stats(zipcode):
	print('Looking up noise statistics for zipcode {}.'.format(zipcode))
	
	surveyData = csv.reader(open("data\Night_Noise_Survey_Manhattan.csv"), delimiter=",")
	surveyData2 = csv.reader(open("data\Noise_Complaints.csv"), delimiter=",")
	surveyData3 = csv.reader(open("data\Noise.csv"), delimiter=",")
	surveyData4 = csv.reader(open("data\DATA_MAP_NOISE_1.csv"), delimiter=",")
	surveyData5 = csv.reader(open("data\Noise_in_NYC.csv"), delimiter=",")
	surveyData6 = csv.reader(open("data\Night_Noise_Survey_CB_3.csv"), delimiter=",")
	surveyData7 = csv.reader(open("data\Commercial_noise.csv"), delimiter=",")



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

	for row in surveyData7:
		zip_count[row[8]] +=1	
	 
	#print zip_count        

	sorted_count=sorted(zip_count,key=zip_count.get,reverse=True) 

	list_len=len(zip_count)
	#print list_len

	#print sorted_count
	diff= int(zip_count[sorted_count[0]])


	for i in range(0,list_len):
		rslt=sorted_count[i]
		#print "% r,% r   " %(rslt,zip_count[str(rslt)])
		if zip_count[rslt] < 500:
			zip_count[rslt]=5
		
		if (zip_count[rslt] >= 500 and zip_count[rslt] < 2000):
			zip_count[rslt]=4
		
		if (zip_count[rslt] >= 2000 and zip_count[rslt] < 5000):
			zip_count[rslt]=3
		
		if (zip_count[rslt] >= 5000 and zip_count[rslt] < 10000):
			zip_count[rslt]=2
		
		if (zip_count[rslt] >= 10000):
			zip_count[rslt]=1
		
		if rslt == str(zipcode):
			print('Found noise stat ranking of {} for zipcode {}.'.format(zip_count[str(rslt)], zipcode))
			return zip_count[str(rslt)]
			
	print('Did not find noise stats for zipcode {}.'.format(zipcode))
	return 0