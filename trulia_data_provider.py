try: import urllib.request as urllib2
except ImportError: import urllib2
import urllib
import xml.etree.ElementTree as et
from utils import *
import keys

TRULIA_KEY = keys.TRULIA_KEY

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
		
	def get_trulia_data_for_year_by_city(self, year, city, state):
		start_date, end_date = get_dates_for_year(year)
		return self.get_trulia_data_for_date_range_and_city(start_date, end_date, city, state)	

	def get_trulia_data_for_quarter_by_city(self, quarter, year, city, state):
		start_date, end_date = get_dates_for_quarter(quarter, year)
		return self.get_trulia_data_for_date_range_and_city(start_date, end_date, city, state)	
		
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
		return tree