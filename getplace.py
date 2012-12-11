import urllib2
import json
import re
import sys

lat = '40.72542280'
long= '-73.98223740'
radius = '300'
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
	x = 0 
	if x <= len(reference_numbers)-1:
		url = 'https://maps.googleapis.com/maps/api/place/details/json?reference=%s&sensor=true&key=%s'% (reference_numbers[x], api_key)
		request = urllib2.urlopen(url)
		results_map = json.loads(request.read())
		place_names.append(results_map['result']['name'])
		x+=1
	return place_names


print get_places((get_reference_number(lat, long, radius, type, api_key)), api_key)