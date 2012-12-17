'''
This code takes the data set "Crime statistics by precinct ",
 to get the count of the total number of crime activities reported for each precinct and then coming up with a score for each precinct.

A score between 1 to 5 is assigned to each precinct depending on the count for each precinct, 5 being the most unsafe precinct and 1 being the safest.
The output of this code is a dictionary having key as the precinct number and value as the safety score.
'''


import json
from collections import defaultdict
import re
import os
import urllib2

u = urllib2.urlopen('https://data.cityofnewyork.us/api/views/yts9-kmw9/rows.json?accessType=DOWNLOAD')
localFile = open('rows.json', 'w')
localFile.write(u.read())

file=open('rows.json','r')
lastnames =[]  # The set usernames stores full names of all customers from every record 

count=defaultdict(int)
for line in file:
	res = re.search('(\d{1,3})([a-z]{2})\s(Precinct)',line,re.DOTALL)
	if res:
		count[res.group(1)] +=1

sorted_count=sorted(count,key=count.get,reverse=True) 

list_len=len(count)


diff= int(sorted_count[0])-int(sorted_count[list_len-1])

for i in range(0,list_len):
	rslt=sorted_count[i]
	if i < diff/5:
		count[rslt]=5
	
	if (i >= diff/5 and i < 2* diff/5):
		count[rslt]=4
	
	if (i >= 2* diff/5 and i < 3* diff/5):
		count[rslt]=3
	
	if (i >= 3* diff/5 and i < 4* diff/5):
		count[rslt]=2
	
	if (i >= 4* diff/5):
		count[rslt]=1
	
		print "% r,% r   " %(rslt,count[str(rslt)])
		
	
file.close()	
