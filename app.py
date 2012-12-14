import pprint
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from zip_data_provider import *
from trulia_data_provider import *
from yelp_data_provider import *
import numpy
from googlemaps import GoogleMaps

yelp = YelpDataProvider(YELP_KEY)
trulia = TruliaDataProvider(TRULIA_KEY)
gmaps = GoogleMaps('AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU')

def get_places(origin, poi_categories, radius_of_interest=300):
	# @tyler: placeholder...
	return {'bar' : ['Cassidy\'s Pub', 'Suite 55'], 'restaurant' : ['Rue 57', 'Chipotle']}
	
def in_range(origin, test_location, acceptable_distance):
	# @tyler: placeholder...
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
	
	trulia_data = trulia.get_trulia_data_for_date_range_and_zipcode(trulia_start_dt, trulia_end_dt, zipcode)
	result = {'poi' : valid_businesses, 'real_estate' : trulia_data}
	print('Collected data: {}'.format(result))
	return result
data = collect_data('1350 Avenue of the Americas, NYC, NY', ['restaurant', 'bar', 'supermarket'], date(2011,1,1), date(2011, 12, 31), date(2012, 1, 1), date(2012, 12, 12))

def graph_data(poi_data, real_estate_data):
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
	
	def plot_data_with_dates(x_list, y_list, format, label_list, title, include_trend=True):
		if len(y_list) != len(label_list):
			raise Exception('# of series to plot does not match # of labels for legend.')
		
		only_plot_trend = include_trend and len(y_list) > 1
		fig = plt.figure()
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
		return plt
	
	def plot_histogram(data, bins, x_label, y_label, title):
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
			plot_data_with_dates(x, y, '-|', l, 'Yelp!').show()		
	
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
		plot_data_with_dates(x, y, '-|', l, 'Yelp!').show()
	
	def graph_category_pricing_histogram():
		for category in business_by_category:
			price_ranges = []
			for business in business_by_category[category]:
				if hasattr(business, 'price_range'):
					price_ranges.append(len(business.price_range))
			plot_histogram(price_ranges, range(0,6,1), 'Price Range', 'Count', 'Yelp!').show()
	
	#graph_business_reviews_by_category_over_time()
	#graph_category_reviews_over_time()
	graph_category_pricing_histogram()
			
graph_data(data['poi'], data['real_estate'])
'''
DEBUG = False
start_date = date(2011,1,1)
end_date = date(2012,12,12)
zipcode = 10019

trulia = TruliaDataProvider(TRULIA_KEY)

city, state = ZipcodeProvider(trulia).get_city_for_zipcode(zipcode)
location = '{}, {} {}'.format(city, state, zipcode)
search_terms = 'bars'

def yelp_test(location, terms):
	results = yelp.getReviewsByLocation(location, search_terms=terms, limit=1)

	fig = plt.figure()
	graph = fig.add_subplot(111)	
	for business in results:
		print('{}'.format(business))
		
		dates = []
		ratings = {}
		
		for review in business.reviews:
			pub_date = mdates.date2num(datetime.strptime(review.pub_date, '%Y-%m-%d'))
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
			
		if len(results) == 1:
			plt.plot_date(dates, sorted_ratings, '-|', label=business.name)		
			
		z = numpy.polyfit(dates, sorted_ratings, len(dates) / 12)
		p = numpy.poly1d(z)
		plt.plot_date(dates,p(dates),'--', label=business.name)
	
	plt.legend(loc=3, prop={'size':8})
	plt.title('Yelp Reviews for \'{}\' in {} ({} Results)'.format(terms, location, len(results)))
	plt.show()
#yelp_test(location, search_terms)

def trulia_test():
	dates = []
	keys = []
	dates_for_keys = {}
	data = {}

	trulia_data = trulia.get_trulia_data_for_date_range_and_zipcode(start_date, end_date, zipcode)
	for listing_stat in trulia_data.findall('./response/TruliaStats/listingStats/listingStat'):
		weekEndingDate = listing_stat.find('weekEndingDate').text
		if weekEndingDate not in dates:
			dates.append(datetime.strptime(weekEndingDate, '%Y-%m-%d'))
		for subcategory in listing_stat.findall('./listingPrice/subcategory'):		
			type = subcategory.find('type').text
			numProperties = subcategory.find('numberOfProperties').text
			medianListing = subcategory.find('medianListingPrice').text
			avgListing = subcategory.find('averageListingPrice').text
			
			datapoint = (numProperties, medianListing, avgListing)
			
			if type not in dates_for_keys:
				dates_for_keys[type] = []
			
			if weekEndingDate not in dates_for_keys[type]:
				dates_for_keys[type].append(weekEndingDate)
			
			if type not in keys:
				keys.append(type)
				
			if type not in data:
				data[type] = []
				
			data[type].append(datapoint)

	if DEBUG:
		pp = pprint.PrettyPrinter(indent=4)
		print pp.pprint(dates_for_keys)

	xdates = mdates.date2num(dates)

	def plotNumProperties():
		fig = plt.figure()
		graph = fig.add_subplot(111)
		for k in keys:
			if k != 'All Properties':
				v = data[k]
				numProperties = []		
				for numProperty, _, _ in v:
					numProperties.append(numProperty)
				if len(dates) < 10:
					graph.plot(mdates.datestr2num(dates_for_keys[k]), numProperties, '-|', label=k)	
				else:
					plt.plot_date(mdates.datestr2num(dates_for_keys[k]), numProperties, '-|', label=k)

		plt.legend(loc=3)
		if len(dates) < 10:
			graph.set_xticks(xdates)
			graph.set_xticklabels([dt.strftime('%Y-%m-%d') for dt in dates])
		plt.title('# Properties Listed for {}, {} {} from {} to {}'.format(city, state, zipcode, start_date, end_date))
		plt.show()

	def plotMedianListings():
		fig = plt.figure()
		graph = fig.add_subplot(111)
		for k in keys:
			if k != 'All Properties':
				v = data[k]
				medianListings = []		
				for _, medianListing, _ in v:
					medianListings.append(medianListing)
				if len(dates) < 10:
					graph.plot(mdates.datestr2num(dates_for_keys[k]), medianListings, '-|', label=k)	
				else:
					plt.plot_date(mdates.datestr2num(dates_for_keys[k]), medianListings, '-|', label=k)

		plt.legend(loc=3)
		if len(dates) < 10:
			graph.set_xticks(xdates)
			graph.set_xticklabels([dt.strftime('%Y-%m-%d') for dt in dates])
		plt.title('Median Listing Prices for {}, {} {} from {} to {}'.format(city, state, zipcode, start_date, end_date))
		plt.show()
		
	def plotAverageListings():
		fig = plt.figure()
		graph = fig.add_subplot(111)
		for k in keys:
			if k != 'All Properties':
				v = data[k]
				averageListings = []		
				for _, _, averageListing in v:
					averageListings.append(averageListing)
				if len(dates) < 10:
					graph.plot(mdates.datestr2num(dates_for_keys[k]), averageListings, '-|', label=k)	
				else:
					plt.plot_date(mdates.datestr2num(dates_for_keys[k]), averageListings, '-|', label=k)

		plt.legend(loc=3)
		if len(dates) < 10:
			graph.set_xticks(xdates)
			graph.set_xticklabels([dt.strftime('%Y-%m-%d') for dt in dates])
		plt.title('Average Listing Prices for {}, {} {} from {} to {}'.format(city, state, zipcode, start_date, end_date))
		plt.show()

	plotNumProperties()
	plotMedianListings()
	plotAverageListings()
#trulia_test()

def combined_test(location, terms):
	results = yelp.getBusinessByName(location, terms)
	if len(results) != 1:
		raise Exception('Unable to find a business for {}'.format(terms))
		
	# check that the given business location is within range of the point of origin and radius
	global zipcode, city, state
	zipcode = results[0].zip	
	city, state = ZipcodeProvider(trulia).get_city_for_zipcode(zipcode)
	print('Using zipcode from Yelp business: {}'.format(zipcode))
	
	fig = plt.figure()
	graph = fig.add_subplot(111)	
	for business in results:
		print('{}'.format(business))
		
		dates = []
		ratings = {}
		
		for review in business.reviews:
			pub_date = mdates.date2num(datetime.strptime(review.pub_date, '%Y-%m-%d'))
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
			
		if len(results) == 1:
			plt.plot_date(dates, sorted_ratings, '-|', label=business.name)		
			
		z = numpy.polyfit(dates, sorted_ratings, len(dates) / 12)
		p = numpy.poly1d(z)
		plt.plot_date(dates,p(dates),'--', label=business.name)
	
	plt.legend(loc=3, prop={'size':8})
	plt.title('Yelp Reviews for \'{}\' in {} ({} Results)'.format(terms, location, len(results)))
	plt.show()
	
	trulia_test()
#combined_test(location, search_terms)
'''