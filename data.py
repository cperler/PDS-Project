try: import urllib.request as urllib2
except ImportError: import urllib2
import urllib
import xml.etree.ElementTree as et
from datetime import date
import re
import json
import os

TRULIA_KEY = 'baq3jbma7dc82f2rtkdwvt7w'
ZIPTASTIC_API = 'http://zip.elevenbasetwo.com/v2/US/{}'
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
	page_request_count += 1
	request = urllib2.urlopen(url)
	response = str(request.read())
	return response

class ZipcodeProvider:
	def get_zipcodes_for_city(self, city, state):
		filename = '{}_{}_zipcodes.txt'.format(city, state)		
		if file_exists(filename):
			print 'Loading zipcodes for {}, {} from file {}.'.format(city, state, filename)
			contents = read_from_file(filename)		
			zipcodes_for_city = []
			for line in contents.split('\n'):
				if line != '':
					zipcodes_for_city.append(line)
			return zipcodes_for_city
		
		print 'Downloading zipcodes for {}, {}.'.format(city, state)
		
		parameters = {}
		parameters['city'] = city
		parameters['state'] = state
		zipcodes_for_state_page = get_trulia_data('LocationInfo', 'getZipCodesInState', parameters)				
		
		zipcodes_for_state = []
		tree = et.fromstring(zipcodes_for_state_page)
		for el in tree.findall('./response/LocationInfo/zipCode'):
			zipcodes_for_state.append(el.find('name').text)
				
		zipcodes_in_city = []
		zipcodes_in_city_content = ''
		for zipcode in zipcodes_for_state:
			print 'Looking up city for zipcode {}...'.format(zipcode)
			city_for_zipcode = self.get_city_for_zipcode(zipcode)
			if city_for_zipcode is not None:
				print 'Found city {} for zipcode {}'.format(city, city_for_zipcode)
				if city_for_zipcode == city:
					zipcodes_in_city_content += zipcode + '\n'
					zipcodes_in_city.append(zipcode)
		write_to_file(filename, zipcodes_in_city_content)
		return zipcodes_in_city
		
	def get_city_for_zipcode(self, zipcode):
		try:
			url = ZIPTASTIC_API.format(zipcode)
			page = get_page(url)
			return json.loads(page)['city']
		except urllib2.HTTPError:
			return 'Unable to locate city for zipcode {}.'.format(zipcode)

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

class TruliaDataProvider:
	TRULIA_API = 'http://api.trulia.com/webservices.php?{}'
	
	def __init__(self, APIKEY):
		self.APIKEY = APIKEY
		
	def get_trulia_data_for_year_by_zipcode(self, year, zipcode):
		start_date, end_date = get_dates_for_year(year)
		return self.get_trulia_data_for_date_range_and_zipcode(start_date, end_date, zipcode)
		
	def get_trulia_data_for_quarter_by_zipcode(self, quarter, year, zipcode):
		start_date, end_date = get_dates_for_quarter(quarter, year)
		return self.get_trulia_data_for_date_range_and_zipcode(start_date, end_date, zipcode)	
		
	def get_trulia_data_for_year_by_city(self, year, city):
		start_date, end_date = get_dates_for_year(year)
		zipcodes = ZipcodeProvider().get_zipcodes_for_city(city)
		
		data = []
		for zipcode in zipcodes:
			data.append(self.get_trulia_data_for_date_range_and_zipcode(start_date, end_date, zipcode))
		return data

	def get_trulia_data_for_quarter_by_city(self, quarter, year, city, state):
		start_date, end_date = get_dates_for_quarter(quarter, year)
		zipcodes = ZipcodeProvider().get_zipcodes_for_city(city, state)

		data = []
		for zipcode in zipcodes:
			data.append(self.get_trulia_data_for_date_range_and_zipcode(start_date, end_date, zipcode))
		return data
		
	def get_trulia_data_for_date_range_and_city(self, start_date, end_date, city, state):
		parameters = {}
		parameters['startDate'] = start_date
		parameters['endDate'] = end_date
		parameters['city'] = city
		parameters['state'] = state
		return self.get_trulia_data('TruliaStats', 'getCityStats', parameters)
			
	def get_trulia_data_for_date_range_and_zipcode(self, start_date, end_date, zipcode):
		parameters = {}	
		parameters['startDate'] = start_date
		parameters['endDate'] = end_date
		parameters['zipCode'] = zipcode		
		return self.get_trulia_data('TruliaStats', 'getZipCodeStats', parameters)

	def get_trulia_data(self, library, function, parameters):
		parameters['library'] = library
		parameters['function'] = function
		parameters['apikey'] = self.APIKEY
		
		query = urllib.urlencode(parameters)
		url = TruliaDataProvider.TRULIA_API.format(query)
		page = get_page(url)
		tree = et.fromstring(page)
		return page

print TruliaDataProvider(TRULIA_KEY).get_trulia_data_for_quarter_by_city('Q4', 2011, 'Mamaroneck', 'NY')
print 'Total Page Requests: {}'.format(page_request_count)