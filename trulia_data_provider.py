try: import urllib.request as urllib2
except ImportError: import urllib2
import urllib
import xml.etree.ElementTree as et
from utils import *
import keys
from datetime import datetime

TRULIA_KEY = keys.TRULIA_KEY

class TruliaDataProvider:
	'''
	A wrapper around the Trulia API - provides helper methods for download data given various 
	input parameters that specify location and date range.
	'''
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
		
	def parse_listings(self, listing_tree):
		listings = []
		for listing_stat in listing_tree.findall('./response/TruliaStats/listingStats/listingStat'):
			weekEndingDate = listing_stat.find('weekEndingDate').text
			for subcategory in listing_stat.findall('./listingPrice/subcategory'):		
				type = subcategory.find('type').text
				numProperties = subcategory.find('numberOfProperties').text
				medianListing = subcategory.find('medianListingPrice').text
				avgListing = subcategory.find('averageListingPrice').text
				
				listing = TruliaListing(weekEndingDate, type, numProperties, medianListing, avgListing)
				listings.append(listing)
		return listings
		
class TruliaListing():
	def __init__(self, weekEndingDate, type, numProperties, medianListing, avgListing):
		self.weekEndingDate = datetime.strptime(weekEndingDate, '%Y-%m-%d')
		self.type = type
		self.numProperties = numProperties
		self.medianListing = medianListing
		self.avgListing = avgListing
	
	def __str__(self):
		return '{} ({}, {} properties)'.format(self.type, self.weekEndingDate, self.numProperties)
		
	def __repr__(self):
		return self.__str__()