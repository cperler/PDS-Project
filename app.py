import matplotlib.pyplot as plt
from pylab import *
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import numpy as np
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
import pprint
from sklearn import linear_model, cross_validation, tree
from crime_reports_by_zip import *
from Noise_complaints_by_zip import *

DEBUG = False
SAVE_PLOTS = True

yelp = YelpDataProvider(YELP_KEY)
trulia = TruliaDataProvider(TRULIA_KEY)
gmaps = GoogleMaps(GOOGLE_KEY)

roi = 400
non_categorical_categories = ['school', 'police', 'park', 'subway_station']
poi_categories = ['restaurant', 'school', 'police', 'park', 'bar', 'subway_station', 'supermarket', 'pharmacy']

address = raw_input('Enter a street address: ')
if address == None or address == '':
	print('Invalid street address, using default: 1350 Avenue of the Americas, NYC, NY')
	address = '1350 Avenue of the Americas, NYC, NY'
	
directory = '.\\' + address.replace(',', '').replace(' ', '_')
if not os.path.exists(directory):
    os.makedirs(directory)

def show_or_save_plot(plot, title):
	if SAVE_PLOTS:		
		savefig(directory + '/' + title + '.png')
		plot.close()
	else:
		plot.show()

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
	lat, lon = get_lat_lon(origin)
	points_of_interest = get_places(lat, lon, poi_categories)
	zipcode = get_zipcode(origin)
	crime_stat_for_zipcode = get_crime_stats(zipcode)
	noise_stat_for_zipcode = get_noise_stats(zipcode)

	valid_businesses = []
	for category in poi_categories:
		if category in points_of_interest and category not in non_categorical_categories:
			for poi in points_of_interest[category]:
				yelp_results = yelp.getReviewsByName(origin, poi, category=category)
					
				if len(yelp_results) == 0:
					try:
						print('Unable to find a Yelp business for {} -- skipping.'.format(poi))
					except UnicodeEncodeError:
						print('Unable to parse a Yelp business details.')
					continue
				elif len(yelp_results) > 1:
					print('Too many results retrieved querying Yelp for {} -- skipping.'.format(poi))
					continue
				
				business = yelp_results[0]
				business.filter_reviews_by_date(yelp_start_dt, yelp_end_dt)
				
				if in_range(origin, business.get_address(), roi):
					valid_businesses.append(business)
	
	landmark_frequencies = {}
	for category in non_categorical_categories:
		landmark_frequencies[category] = points_of_interest[category]
		
	print('Collected data from yelp.')
		
	trulia_data = trulia.parse_listings(trulia.get_trulia_data_for_date_range_and_zipcode(trulia_start_dt, trulia_end_dt, zipcode))
	print('Collected data from trulia.')
	
	result = {	
				'poi' : valid_businesses, 
				'landmark_frequencies' : landmark_frequencies,
				'crime_stat' : crime_stat_for_zipcode,
				'noise_stat' : noise_stat_for_zipcode,
				'real_estate' : trulia_data, 
				'origin' : origin, 
				'zipcode' : zipcode,
				'dates' : {
					'yelp' : {'start' : yelp_start_dt, 'end' : yelp_end_dt},
					'trulia' : {'start' : trulia_start_dt, 'end' : trulia_end_dt}
				}
			}
				
	return result

def graph_data(poi_data, real_estate_data, landmark_frequencies, origin, zipcode, yelp_dates, trulia_dates):
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
				p = np.poly1d(np.polyfit(x, y, 4))
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
								
			show_or_save_plot(plot_data_with_dates(x, y, 'Review Date', 'Business Ranking (Trend)', '-|', l, graph_title), graph_title)
			
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
		
		show_or_save_plot(plot_data_with_dates(x, y, 'Review Date', 'Category Ranking Avg (Trend)', '-|', l, graph_title), graph_title)
	
	def graph_category_pricing_histogram():
		for category in business_by_category:
			price_ranges = []
			for business in business_by_category[category]:
				if hasattr(business, 'price_range'):
					price_ranges.append(len(business.price_range))
					
			yelp_start_dt = yelp_dates['start']
			yelp_end_dt = yelp_dates['end']
			graph_title = no_dates_title.format('Yelp Category Price Range Histogram for \'{}\''.format(category), yelp_start_dt, yelp_end_dt)		
					
			show_or_save_plot(plot_histogram(price_ranges, range(0,6,1), 'Price Range (# Dollar Signs)', 'Frequency', graph_title), graph_title)
			
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
		show_or_save_plot(plot_data_with_dates(dates_for_keys.values(), numProperties_data.values(), 'Week Ending Date', 'Count', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False), graph_title)
		
		graph_title = title.format('Median Trulia Real Estate Prices', trulia_start_dt, trulia_end_dt)
		show_or_save_plot(plot_data_with_dates(dates_for_keys.values(), medianListing_data.values(), 'Week Ending Date', 'Median Listing Price ($)', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False), graph_title)
		
		graph_title = title.format('Average Trulia Real Estate Prices', trulia_start_dt, trulia_end_dt)
		show_or_save_plot(plot_data_with_dates(dates_for_keys.values(), avgListing_data.values(), 'Week Ending Date', 'Avg Listing Price ($)', 
			'-|', dates_for_keys.keys(), graph_title, include_trend=False), graph_title)
	
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
			p = np.poly1d(np.polyfit(x, y, 4))
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
		show_or_save_plot(plt, graph_title)

	graph_business_reviews_by_category_over_time()
	graph_category_reviews_over_time()
	graph_category_pricing_histogram()
	try:
		graph_properties_over_time()
		graph_category_reviews_vs_real_estate_prices()
	except ValueError:
		pass
	return business_by_category

def analyze_data(business_by_category, poi_data, real_estate_data, landmark_frequencies, crime_stat, noise_stat, origin, zipcode, yelp_dates, trulia_dates):
	predictions = {}
	yelp_x, yelp_y = [], []	
	yelp_data = {}
	category_idx = 0
	max_yelp_dt = 0
	for category in business_by_category:
		dates = []
		ratings = {}
		for business in business_by_category[category]:
			for review in business.reviews:
				pub_date = mdates.date2num(review.pub_date)
				if pub_date > max_yelp_dt:
					max_yelp_dt = pub_date
					
				rating = float(review.rating)
			
				if pub_date not in dates:
					dates.append(pub_date)
			
				if pub_date not in ratings:
					ratings[pub_date] = rating
				else:
					ratings[pub_date] = (ratings[pub_date] + rating) / 2.0
	
		dates.sort()

		for dt in dates:
			if dt not in yelp_data:
				yelp_data[dt] = []
				for idx in range(0, category_idx, 1):
					yelp_data[dt].append(0)
			yelp_data[dt].append(ratings[dt])
			
		for dt in yelp_data:
			while len(yelp_data[dt]) <= category_idx:
				yelp_data[dt].append(0)

		idx = 0
		while idx <= category_idx:			
			last_val = 0
			for dt in dates:
				if yelp_data[dt][idx] == 0:
					yelp_data[dt][idx] = last_val
				else:
					last_val = yelp_data[dt][idx]
			idx += 1			

		dates.reverse()
			
		idx = 0
		while idx <= category_idx:			
			last_val = 0
			for dt in dates:
				if yelp_data[dt][idx] == 0:
					yelp_data[dt][idx] = last_val
				else:
					last_val = yelp_data[dt][idx]
			idx += 1			
		category_idx += 1
	
	trulia_x, trulia_y = [], []
	
	dates_for_keys = {}
	avgListing_data = {}
	
	all_types = []
	for listing in real_estate_data:
		type = listing.type
		if type not in all_types:
			all_types.append(type)

	def find_trulia_data(trulia_data, start_date, days_out):
		target_dt = start_date + days_out
		for k, v in trulia_data:
			if k >= target_dt:
				return (k, v)
		return (None, None)
			
	for trulia_type in all_types:
		for listing in real_estate_data:
			type = listing.type
			if type == trulia_type:
				weekEndingDate = listing.weekEndingDate
				avgListing = listing.avgListing
				
				if type not in dates_for_keys:
					dates_for_keys[type] = []
				
				if weekEndingDate not in dates_for_keys[type]:
					dates_for_keys[type].append(mdates.date2num(weekEndingDate))
				
				if type not in avgListing_data:
					avgListing_data[type] = []
					
				avgListing_data[type].append(int(avgListing))
				
		trulia_x = dates_for_keys[trulia_type]
		trulia_y = avgListing_data[trulia_type]		
		trulia_data = zip(trulia_x, trulia_y)
		trulia_data.sort()
		
		lookahead_x = []
		accuracy_y = []
		lookaheads = range(0, 390, 30)
		targets = [float(target) / 100.0 for target in range(5, 100, 5)]
		trained_accuracy_y = []
		x_current = []
		for lookahead in lookaheads:	
			x = []
			y = []
			for yelp_x, yelp_y in yelp_data.items():
				_, current_trulia_y = find_trulia_data(trulia_data, yelp_x, 0)
				trulia_x, trulia_y = find_trulia_data(trulia_data, yelp_x, lookahead)
				if trulia_x is not None:
					x_dt = int(yelp_x) - max_yelp_dt
					x_val = [x_dt] + yelp_y + [crime_stat] + [noise_stat] + [v for k, v in landmark_frequencies.items()]
					if x_dt == 0:
						x_current = x_val
					else:
						x.append(x_val)
						y.append(trulia_y)		
					
					# if we were to reverse the matrix, and use prices as a predictor of average yelp reviews:
					# x.append([(int(yelp_x) - max_yelp_dt)] + [trulia_y] + [crime_stat] + [noise_stat] + [v for k, v in landmark_frequencies.items()])
					# y.append(sum(yelp_y) / len(yelp_y))
			
			x = np.array(x)
			y = np.array(y)
			
			lr = linear_model.LinearRegression()			
			lr_scores = cross_validation.cross_val_score(lr, x, y, cv=10)
			
			if DEBUG:
				print "lr accuracy: %0.2f (+/- %0.3f)" % (lr_scores.mean(), lr_scores.std() / 2)
				print "lr error rate = %0.2f" % (1 - lr_scores.mean())			

			lookahead_x.append(lookahead)
			accuracy_y.append(lr_scores.mean())
			
			training_accuracy_for_target = []
			for target in targets:
				x_train, x_test, y_train, y_test = cross_validation.train_test_split(x, y, test_size=target, random_state=0)
				lr = lr.fit(x_train, y_train)
				lr_score = lr.score(x_test, y_test)
				training_accuracy_for_target.append(lr_score)
			trained_accuracy_y.append(training_accuracy_for_target)
			
			if trulia_type not in predictions:
				predictions[trulia_type] = {}
			try:
				prediction = lr.predict(x_current)
				predictions[trulia_type][lookahead] = {}
				if (trulia_type == '1 Bedroom Properties' or trulia_type == '2 Bedroom Properties' or trulia_type == '3 Bedroom Properties') and lookahead == 360:
					print('Prediction for {}..'.format(trulia_type))
					print('\t{}'.format(int(prediction)))
					print('\tCoefficients: {}'.format(lr.coef_))
				predictions[trulia_type][lookahead]['prediction'] = int(prediction)
				predictions[trulia_type][lookahead]['coefficient'] = lr.coef_
			except ValueError:
				predictions[trulia_type][lookahead] = -1
			
		plt.plot(lookahead_x, accuracy_y)
		graph_title = 'Linear Regression Mean Using {}'.format(trulia_type)
		plt.title(graph_title)
		plt.xlabel('lookahead period')
		plt.ylabel('cross validation score - mean')
		show_or_save_plot(plt, graph_title)
		
		for lookahead, training_accuracy_for_target in zip(lookaheads, trained_accuracy_y):
			plt.plot(targets, training_accuracy_for_target, label=('lookahead ' + str(lookahead)))
		graph_title = 'Trained Linear Regression Using {}'.format(trulia_type)
		plt.title(graph_title)
		plt.legend(loc=3, prop={'size':8})
		plt.xlabel('% test in target')
		plt.ylabel('% accuracy')
		show_or_save_plot(plt, graph_title)

	return predictions

yelp_start_dt = date(2011, 1, 1)
yelp_end_dt = date(2012, 9, 12)
trulia_start_dt = date(2011, 1, 1)
trulia_end_dt = date(2012, 12, 12)
trulia_end_dt_minus_1_week = date(2012, 12, 5)

if DEBUG:	
	data = pickle_load('datums')
	business_by_category = pickle_load('business_by_category')
else:
	data = collect_data(address, poi_categories, yelp_start_dt, yelp_end_dt, trulia_start_dt, trulia_end_dt)
	pickle_it('datums', data)
	
	business_by_category = graph_data(data['poi'], data['real_estate'], data['landmark_frequencies'], data['origin'], data['zipcode'], data['dates']['yelp'], data['dates']['trulia'])
	pickle_it('business_by_category', business_by_category)

predictions = analyze_data(business_by_category, data['poi'], data['real_estate'], data['landmark_frequencies'], data['crime_stat'], data['noise_stat'], data['origin'], data['zipcode'], data['dates']['yelp'], data['dates']['trulia'])

current_prices = {}
current_listing_info = trulia.parse_listings(trulia.get_trulia_data_for_date_range_and_zipcode(trulia_end_dt_minus_1_week, trulia_end_dt, data['zipcode']))
for listing in current_listing_info:
	type = listing.type	
	avgListing = listing.avgListing
	current_prices[type] = avgListing

results = {
	'predictions' : predictions,
	'origin' : data['origin'],
	'zipcode' : data['zipcode'],
	'trulia' : current_prices
}

if DEBUG:
	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(results)
	
file = open(directory + '/' + data['origin'] + '_results.pkl', 'w+')
pickle.dump(results, file)
file.close()

pprint.pprint(results, open(directory + '/' + data['origin'] + '_results.pp', 'w+'))

file = open(directory + '/' + data['origin'] + '_results.out', 'w+')
file.write(str(results))
file.close()