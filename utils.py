try: import urllib.request as urllib2
except ImportError: import urllib2
import urllib
from datetime import date
import re
import json
import os

DATA_PATH = '.\\data\\'

page_request_count = 0

def write_to_file(filename, content, path=DATA_PATH):
	file = open(path+filename, 'w')
	file.write(content)
	file.close()

def read_from_file(filename, path=DATA_PATH):
	file = open(path+filename, 'r')
	contents = file.read()
	return contents
	
def file_exists(filename, path=DATA_PATH):
	print 'Looking up file {}...'.format(path+filename)
	try:
		with open(path+filename, 'r') as f:
			print 'File exists.'
			return True
	except IOError as e:
		print 'File does not exist.'
		return False

def get_page(url):
	global page_request_count
	print 'Loading data from {}.'.format(url)
	page_request_count += 1
	request = urllib2.urlopen(url)
	response = str(request.read())
	print 'Total Page Requests: {}'.format(page_request_count)
	return response

class Quarter:
	def __init__(self, string, start_month, start_day, end_month, end_day):
		self.string = string
		self.start_month = start_month
		self.start_day = start_day
		self.end_month = end_month
		self.end_day = end_day
	
	def get_date_range(self, year):
		return (date(year, self.start_month, self.start_day), date(year, self.end_month, self.end_day))

Q1 = Quarter('Q1', 1, 1, 3, 31)
Q2 = Quarter('Q2', 4, 1, 6, 30)
Q3 = Quarter('Q3', 7, 1, 9, 30)
Q4 = Quarter('Q4', 10, 1, 12, 31)
QUARTERS = {Q1, Q2, Q3, Q4}

def validate_year(year):	
	pattern = '\d{4}'
	match = re.search(pattern, str(year))
	if not match:
		raise Exception('Invalid year {} specified.'.format(year))
			
def get_dates_for_quarter(quarter, year):
	validate_year(year)
	
	for quarter_info in QUARTERS:
		if quarter_info.string == quarter:
			return quarter_info.get_date_range(year)

	raise Exception('Invalid quarter {} specified.'.format(quarter))

def get_dates_for_year(year):
	validate_year(year)	
	return (date(year, 1, 1), date(year, 12, 31))