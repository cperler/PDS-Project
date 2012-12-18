import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import numpy
from datetime import datetime
from zip_data_provider import *
from trulia_data_provider import *
from yelp_data_provider import *
from utils import *
from googlemaps import GoogleMaps
import urllib2
import json
import re
import sys
from keys import *

yelp = YelpDataProvider(YELP_KEY)
trulia = TruliaDataProvider(TRULIA_KEY)
gmaps = GoogleMaps(GOOGLE_KEY)

roi = 700
poi_categories = ['restaurant', 'school', 'police', 'park', 'bar', 'subway_station']
address = '1350 Avenue of the Americas, NYC, NY'
yelp_start_dt = date(2011,1,1)
yelp_end_dt = date(2012, 12, 12)
trulia_start_dt = date(2011, 1, 1)
trulia_end_dt = date(2012, 12, 12)

def get_places(lat, long, poi_categories, radius_of_interest=roi, api_key = GOOGLE_KEY):
	place_name_dict={}
	for type in poi_categories:
		filename = '{}_{}_{}_places.txt'.format(lat, long, type)
		if file_exists(filename):
			print 'Loading places for {} from file {}.'.format(type, filename)
			place_name_dict[type] = pickle_load(filename)
		else:
			url = 'https://maps.googleapis.com/maps/api/place/radarsearch/json?location=%s,%s&radius=%s&types=%s&sensor=false&key=%s'% (lat, long, radius_of_interest, type, api_key)
			print('Loading {}.'.format(url))
			request = urllib2.urlopen(url)
			results_map = json.loads(request.read())
			reference_numbers=[]
			for item in results_map['results']:
				reference_numbers.append(item['reference'])
			place_names=[]
			for numbers in reference_numbers:
				new_url = 'https://maps.googleapis.com/maps/api/place/details/json?reference=%s&sensor=true&key=%s'% (numbers, api_key)
				new_request = urllib2.urlopen(new_url)
				new_results_map = json.loads(new_request.read())
				place_names.append(new_results_map['result']['name'])
			pickle_it(filename, place_names)
			place_name_dict[type]=place_names
		if 'police' in place_name_dict:
			if place_name_dict['police'] != []:
				place_name_dict['police'] = 1 
			else:
				place_name_dict['police'] = 0
		if 'subway_station' in place_name_dict:
			if place_name_dict['subway_station'] != []:
				place_name_dict['subway_station'] = 1 
			else:
				place_name_dict['subway_station'] = 0
		if 'school' in place_name_dict:
			if place_name_dict['school'] != []:
				place_name_dict['school'] = 1 
			else:
				place_name_dict['school'] = 0
		if 'park' in place_name_dict:
			if place_name_dict['park'] != []:
				place_name_dict['park'] = 1 
			else:
				place_name_dict['park'] = 0	
	return place_name_dict

def get_lat_lon(location):
	lat, lon = gmaps.address_to_latlng(location)
	return (lat, lon)
	
def in_range(origin, test_location, acceptable_distance):
	formatted_origin = origin.replace(',', '').replace('&', '').replace(' ', '+').replace('++', '+')
	formatted_test = test_location.replace(',', '').replace('&', '').replace(' ', '+').replace('++', '+')
	url = 'http://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&sensor=false' % (formatted_origin, formatted_test)
	print('Loading {}.'.format(url))
	request = urllib2.urlopen(url)
	results_map = json.loads(request.read())
	meters = None
	for results in results_map['rows']:
		for elements in results['elements']:
			if elements['status'] == 'OK':
				meters = elements['distance']['value']
			else:
				return False
	if meters is not None and meters>acceptable_distance:
		return False
	else:
		return True

def get_zipcode(address):
	normalized_address = gmaps.geocode(address)
	placemark = normalized_address['Placemark'][0]
	return placemark['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['DependentLocality']['PostalCode']['PostalCodeNumber']

def collect_data(origin, poi_categories, yelp_start_dt, yelp_end_dt, trulia_start_dt, trulia_end_dt):
	# 1. get list of businesses within area
	# 2. get zipcode for origin
	# 3. for each business, download yelp data - only load if business zip matches origin zip
	# 4. get trulia data for zipcode
	
	do_not_chart_categories = ['school', 'police', 'park', 'subway_station']
	lat, lon = get_lat_lon(origin)
	points_of_interest = get_places(lat, lon, poi_categories)
	zipcode = get_zipcode(origin)

	valid_businesses = []
	for category in poi_categories:
		if category in points_of_interest and category not in do_not_chart_categories:
			for poi in points_of_interest[category]:
				yelp_results = yelp.getReviewsByName(origin, poi, category=category)
					
				if len(yelp_results) == 0:
					print('Unable to find a Yelp business for {} -- skipping.'.format(poi))
					continue
				elif len(yelp_results) > 1:
					print('Too many results retrieved querying Yelp for {} -- skipping.'.format(poi))
					continue
				
				business = yelp_results[0]
				business.filter_reviews_by_date(yelp_start_dt, yelp_end_dt)
				
				if in_range(origin, business.get_address(), roi):
					valid_businesses.append(business)
	print('Collected data from yelp.')
		
	trulia_data = trulia.parse_listings(trulia.get_trulia_data_for_date_range_and_zipcode(trulia_start_dt, trulia_end_dt, zipcode))
	print('Collected data from trulia.')
	
	result = {	
				'poi' : valid_businesses, 
				'real_estate' : trulia_data, 
				'origin' : origin, 
				'zipcode' : zipcode,
				'dates' : {
					'yelp' : {'start' : yelp_start_dt, 'end' : yelp_end_dt},
					'trulia' : {'start' : trulia_start_dt, 'end' : trulia_end_dt}
				}
			}
				
	return result

def graph_data(poi_data, real_estate_data, origin, zipcode, yelp_dates, trulia_dates):
	business_by_category = {}
	for business in poi_data:
		if business.category not in business_by_category:
			business_by_category[business.category] = []
		business_by_category[business.category].append(business)
	
	def plot_data_with_dates(x_list, y_list, x_label, y_label, format, label_list, title, include_trend=True):
		if len(y_list) != len(label_list):
			raise Exception('# of series to plot does not match # of labels for legend.')
		
		only_plot_trend = include_trend and len(y_list) > 1
		fig = plt.figure(figsize=(6*3.13,4*3.13))
		graph = fig.add_subplot(111)

		data = zip(x_list, y_list, label_list)
		
		for x, y, label in data:
			if not only_plot_trend:
				plt.plot_date(x, y, format, label=label)
			if include_trend:
				p = numpy.poly1d(numpy.polyfit(x, y, 4))
				plt.plot_date(x, p(x), '--', label=label)
		plt.legend(loc=3, prop={'size':8})
		plt.title(title)
		plt.xlabel(x_label)
		plt.ylabel(y_label)
		return plt
	
	def plot_histogram(data, bins, x_label, y_label, title):
		plt.figure(figsize=(6*3.13,4*3.13))
		plt.hist(data, bins=bins)
		plt.xlabel(x_label)
		plt.ylabel(y_label)
		plt.title(title)
		plt.grid(True)
		return plt
		
	def graph_business_reviews_by_category_over_time():
		for category in business_by_category:
			x, y, l = [], [], []
			for business in business_by_category[category]:
				dates = []
				ratings = {}
						
				for review in business.reviews:
					pub_date = mdates.date2num(review.pub_date)
					rating = float(review.rating)
				
					if pub_date not in dates:
						dates.append(pub_date)
				
					if pub_date not in ratings:
						ratings[pub_date] = rating
					else:
						ratings[pub_date] = (ratings[pub_date] + rating) / 2.0
		
				dates.sort()
				sorted_ratings = []

				for dt in dates:
					sorted_ratings.append(ratings[dt])
				
				if len(dates) > 0:
					x.append(dates)
					y.append(sorted_ratings)
					l.append(business.name)
				else:
					print('Skipping {} as it has no data.'.format(business.name))
			
			yelp_start_dt = yelp_dates['start']
			yelp_end_dt = yelp_dates['end']
			graph_title = title.format('Average Yelp Reviews for Category \'{}\''.format(category), yelp_start_dt, yelp_end_dt)
						
			plot_data_with_dates(x, y, 'Review Date', 'Business Ranking (Trend)', '-|', l, graph_title).show()			
	
	def graph_category_reviews_over_time():
		x, y, l = [], [], []
		for category in business_by_category:		
			dates = []
			ratings = {}
			for business in business_by_category[category]:
				for review in business.reviews:
					pub_date = mdates.date2num(review.pub_date)
					rating = float(review.rating)
				
					if pub_date not in dates:
						dates.append(pub_date)
				
					if pub_date not in ratings:
						ratings[pub_date] = rating
					else:
						ratings[pub_date] = (ratings[pub_date] + rating) / 2.0
		
			dates.sort()
			sorted_ratings = []

			for dt in dates:
				sorted_ratings.append(ratings[dt])
			
			x.append(dates)
			y.append(sorted_ratings)
			l.append(category)
		
		yelp_start_dt = yelp_dates['start']
		yelp_end_dt = yelp_dates['end']
		graph_title = title.format('Yelp Category Comparisons', yelp_start_dt, yelp_end_dt)		
		
		plot_data_with_dates(x, y, 'Review Date', 'Category Ranking Avg (Trend)', '-|', l, graph_title).show()
	
	def graph_category_pricing_histogram():
		for category in business_by_category:
			price_ranges = []
			for business in business_by_category[category]:
				if hasattr(business, 'price_range'):
					price_ranges.append(len(business.price_range))
					
			yelp_start_dt = yelp_dates['start']
			yelp_end_dt = yelp_dates['end']
			graph_title = no_dates_title.format('Yelp Category Price Range Histogram for \'{}\''.format(category), yelp_start_dt, yelp_end_dt)		
					
			plot_histogram(price_ranges, range(0,6,1), 'Price Range (# Dollar Signs)', 'Frequency', graph_title).show()
			
	def graph_properties_over_time():
		dates = []
		dates_for_keys = {}
		numProperties_data = {}
		medianListing_data = {}
		avgListing_data = {}
		
		for listing in real_estate_data:
			type = listing.type
			if type != 'All Properties':
				weekEndingDate = listing.weekEndingDate
				if weekEndingDate not in dates:
					dates.append(weekEndingDate)

				numProperties = listing.numProperties
				medianListing = listing.medianListing
				avgListing = listing.avgListing
				
				if type not in dates_for_keys:
					dates_for_keys[type] = []
				
				if weekEndingDate not in dates_for_keys[type]:
					dates_for_keys[type].append(weekEndingDate)
				
				if type not in numProperties_data:
					numProperties_data[type] = []
				if type not in medianListing_data:
					medianListing_data[type] = []
				if type not in avgListing_data:
					avgListing_data[type] = []
					
				numProperties_data[type].append(numProperties)
				medianListing_data[type].append(medianListing)
				avgListing_data[type].append(avgListing)

		trulia_start_dt = trulia_dates['start']
		trulia_end_dt = trulia_dates['end']
		
		graph_title = title.format('Number of Trulia Listings', trulia_start_dt, trulia_end_dt)
		plot_data_with_dates(dates_for_keys.values(), numProperties_data.values(), 'Week Ending Date', 'Count', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False).show()
		
		graph_title = title.format('Median Trulia Real Estate Prices', trulia_start_dt, trulia_end_dt)
		plot_data_with_dates(dates_for_keys.values(), medianListing_data.values(), 'Week Ending Date', 'Median Listing Price ($)', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False).show()
		
		graph_title = title.format('Average Trulia Real Estate Prices', trulia_start_dt, trulia_end_dt)
		plot_data_with_dates(dates_for_keys.values(), avgListing_data.values(), 'Week Ending Date', 'Avg Listing Price ($)', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False).show()
	
	no_dates_title = '{} for zipcode ' + zipcode
	title = no_dates_title + ' - {} to {}'
	
	def graph_category_reviews_vs_real_estate_prices():
		x, y, l = [], [], []
		for category in business_by_category:		
			dates = []
			ratings = {}
			for business in business_by_category[category]:
				for review in business.reviews:
					pub_date = mdates.date2num(review.pub_date)
					rating = float(review.rating)
				
					if pub_date not in dates:
						dates.append(pub_date)
				
					if pub_date not in ratings:
						ratings[pub_date] = rating
					else:
						ratings[pub_date] = (ratings[pub_date] + rating) / 2.0
		
			dates.sort()
			sorted_ratings = []

			for dt in dates:
				sorted_ratings.append(ratings[dt])
			
			x.append(dates)
			y.append(sorted_ratings)
			l.append(category)
	
		fig = plt.figure(figsize=(6*3.13,4*3.13))
		graph = fig.add_subplot(111)

		data = zip(x, y, l)
		for x, y, label in data:
			p = numpy.poly1d(numpy.polyfit(x, y, 4))
			graph.plot_date(x, p(x), '--', label=label)
		graph.set_xlabel('time')
		graph.set_ylabel('average score by category')
		
		x = []
		y = []
		l = []
			
		dates_for_keys = {}
		avgListing_data = {}
		
		for listing in real_estate_data:
			type = listing.type
			if type != 'All Properties':
				weekEndingDate = listing.weekEndingDate
				avgListing = listing.avgListing
				
				if type not in dates_for_keys:
					dates_for_keys[type] = []
				
				if weekEndingDate not in dates_for_keys[type]:
					dates_for_keys[type].append(weekEndingDate)
				
				if type not in avgListing_data:
					avgListing_data[type] = []
					
				avgListing_data[type].append(avgListing)
				
		for type in avgListing_data.keys():
			x.append(dates_for_keys[type])
			y.append(avgListing_data[type])
			l.append(type)
	
		ax2 = graph.twinx()
	
		data = zip(x, y, l)		
		for x, y, label in data:			
			ax2.plot_date(x, y, '-|', label=label)
		graph.set_xlabel('time')
		graph.set_ylabel('average real estate prices')
		
		graph.legend(loc=0, prop={'size':8})
		ax2.legend(loc=2, prop={'size':8})
		
		yelp_start_dt = yelp_dates['start']
		trulia_end_dt = trulia_dates['end']
		
		graph_title = title.format('Yelp Reviews vs Trulia Real Estate Prices', yelp_start_dt, trulia_end_dt)
		plt.title(graph_title)
		plt.show()
	
	graph_business_reviews_by_category_over_time()
	graph_category_reviews_over_time()
	graph_category_pricing_histogram()
	graph_properties_over_time()
	graph_category_reviews_vs_real_estate_prices()

def analyze_data(poi_data, real_estate_data, origin, zipcode, yelp_dates, trulia_dates):
	pass
	
data = collect_data(address, poi_categories, yelp_start_dt, yelp_end_dt, trulia_start_dt, trulia_end_dt)
graph_data(data['poi'], data['real_estate'], data['origin'], data['zipcode'], data['dates']['yelp'], data['dates']['trulia'])
analyze_data(data['poi'], data['real_estate'], data['origin'], data['zipcode'], data['dates']['yelp'], data['dates']['trulia'])