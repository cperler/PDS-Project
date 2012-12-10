import json
import os
import xml.etree.ElementTree as et
from utils import *

ZIPTASTIC_API = 'http://zip.elevenbasetwo.com/v2/US/{}'

class ZipcodeProvider:
	def __init__(self, trulia_data_provider):
		self.trulia_data_provider = trulia_data_provider
		
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
		zipcodes_for_state_page = self.trulia_data_provider.get_trulia_data('LocationInfo', 'getZipCodesInState', parameters)				
		
		zipcodes_for_state = []
		for el in zipcodes_for_state_page.findall('./response/LocationInfo/zipCode'):
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
			json_from_page = json.loads(page)
			return (json_from_page['city'], json_from_page['state'])
		except urllib2.HTTPError:
			return 'Unable to locate city for zipcode {}.'.format(zipcode)
