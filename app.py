import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy
from datetime import datetime
from zip_data_provider import *
from trulia_data_provider import *
from yelp_data_provider import *
from googlemaps import GoogleMaps
import urllib2
import json
import re
import sys

yelp = YelpDataProvider(YELP_KEY)
trulia = TruliaDataProvider(TRULIA_KEY)
gmaps = GoogleMaps('AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU')


lat = '40.72542280'
long= '-73.98223740'
radius = '300'
api_key = 'AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU'
poi_categories = ['restaurant', 'school', 'police+station', 'firehouse', 'bar', 'subway+station']

def get_places(lat, long, poi_categories, radius_of_interest=300, api_key ='AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU'):
	place_name_dict={}
	for type in poi_categories:
		url = 'https://maps.googleapis.com/maps/api/place/radarsearch/json?location=%s,%s&radius=%s&types=%s&sensor=false&key=%s'% (lat, long, radius_of_interest, type, api_key)
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
		place_name_dict[type]=place_names
	return place_name_dict

	
def in_range(origin, test_location, acceptable_distance):
	url = 'http://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&sensor=false' % (origin, test)
	request = urllib2.urlopen(url)
	results_map = json.loads(request.read())
	for results in results_map['rows']:
		for elements in results['elements']:
			meters = elements['distance']['value']
	if meters>distance:
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
	
	points_of_interest = get_places(origin, poi_categories)
	zipcode = get_zipcode(origin)

	valid_businesses = []
	for category in poi_categories:
		if category in points_of_interest:
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
				
				if in_range(origin, business.get_address(), 400):
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
data = collect_data('1350 Avenue of the Americas, NYC, NY', ['restaurant', 'bar', 'supermarket'], date(2011,1,1), date(2011, 12, 31), date(2012, 1, 1), date(2012, 12, 12))

def graph_data(poi_data, real_estate_data, origin, zipcode, yelp_dates, trulia_dates):
	# 1. graph business reviews / category over time
	# 2. graph category reviews over time
	# 3. graph category pricing histogram
	# 4. graph number of properties per type over time
	# 5. graph median listing per type over time
	# 6. graph average listing per type over time
	
	# 7. graph category reviews vs average listing per type over time
	# 8. graph category pricigin vs number of properties per type over time
	
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
				p = numpy.poly1d(numpy.polyfit(x, y, max(1, len(x) / 12)))
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
				
				x.append(dates)
				y.append(sorted_ratings)
				l.append(business.name)
			
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
			
	def graph_num_properties_over_time():
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
	
	graph_business_reviews_by_category_over_time()
	graph_category_reviews_over_time()
	graph_category_pricing_histogram()
	graph_num_properties_over_time()
			
graph_data(data['poi'], data['real_estate'], data['origin'], data['zipcode'], data['dates']['yelp'], data['dates']['trulia'])
