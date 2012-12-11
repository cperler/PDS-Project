import urllib2
import json
import re
import sys

lat = '40.72542280'
long= '-73.98223740'
radius = '200'
api_key = 'AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU'
type = 'restaurant'

def get_reference_number(lat, long, radius, type, api_key):
  url = 'https://maps.googleapis.com/maps/api/place/radarsearch/json?location=%s,%s&radius=%s&types=%s&sensor=false&key=%s'% (lat, long, radius, type, api_key)
	request = urllib2.urlopen(url)
	results_map = json.loads(request.read())
	reference_numbers=[]
	for item in results_map['results']:
		 reference_numbers.append(item['reference'])
	return reference_numbers
	
def get_places(reference_numbers, api_key):
	place_names=[]
	for reference_number in reference_numbers:
		url = 'https://maps.googleapis.com/maps/api/place/details/json?reference=%s&sensor=true&key=%s'% (reference_number, api_key)
		request = urllib2.urlopen(url)
		results_map = json.loads(request.read())
		for item in results_map['result']:
			print item['name']
			#place_names.append(place_name)
	#return place_names


print get_places((get_reference_number(lat, long, radius, type, api_key)), api_key)