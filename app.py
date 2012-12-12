import pprint
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from zip_data_provider import *
from trulia_data_provider import *
from yelp_data_provider import *

DEBUG = False
start_date = date(2012,1,1)
end_date = date(2012,12,10)
zipcode = 10019

trulia = TruliaDataProvider(TRULIA_KEY)
yelp = YelpDataProvider(YELP_KEY)
city, state = ZipcodeProvider(trulia).get_city_for_zipcode(zipcode)
location = '{}, {} {}'.format(city, state, zipcode)

def yelp_test():
	results = yelp.getReviewsByLocation(location, search_terms='bars', limit=3)
	for business in results:
		print('{}'.format(business))
yelp_test()

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