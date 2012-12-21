from yelp import ReviewSearchApi
from utils import *
import keys
from datetime import datetime

YELP_KEY = keys.YELP_KEY

class YelpDataProvider():	
	'''
	A wrapper around the Yelp python plugin, which itself is a helper utility for accessing the Yelp API.
	
	This provider can return a set of YelpBusiness instances, each of which contains data pulled from both the Yelp API and
	scraped from the web, including paginated reviews.  Each YelpBusiness has a list of YelpReviews, each of which represents
	a single scraped review.
	'''
	def __init__(self, APIKEY):
		self.APIKEY = APIKEY
		
	def getReviewsByName(self, location, business_name, category=None, radius=.400, limit=1):
		businesses = self.getReviewsByLocation(location, radius, business_name, limit, category=category)
		return businesses
		
	def getReviewsByLocation(self, location, radius=1, search_terms='', limit=20, category=None):
		search_terms = removeNonAscii(search_terms)
		filename = '{}_{}_{}_{}_reviews.txt'.format(location, search_terms, category, limit)
		if file_exists(filename):
			print 'Loading {} reviews for {} - {} from file {}.'.format(limit, location, search_terms, filename)
			return pickle_load(filename)
		
		results = ReviewSearchApi(client_key=self.APIKEY, output='json').by_location(location, term=search_terms, radius=radius, num_biz_requested=limit, category=category)
		if results['message']['text'] != 'OK':
			raise Exception('Error retrieving Yelp results.')
			
		businesses = []
		for result in results['businesses']:
			business = YelpBusiness(result, category)
			businesses.append(business)
		try:
			pickle_it(filename, businesses)
		except IOError:
			print('Unable to pickle a Yelp business.')
		return businesses
		
class YelpBusiness():
	PRICE_RANGE_RE = '>(\$+)<'
	REVIEW_RATINGS_RE = 'ratingValue\" content\=\"(.*?)\"'
	REVIEW_PUBLISHED_RE = 'datePublished\" content\=\"(.*?)\"'
	
	def __init__(self, result_from_query, category):
		self.id = result_from_query['id']
		self.name = result_from_query['name']
		self.url = result_from_query['url']
		self.latitude = result_from_query['latitude']
		self.longitude = result_from_query['longitude']
		self.avg_rating = result_from_query['avg_rating']
		self.review_count = result_from_query['review_count']
		self.address1 = result_from_query['address1']
		self.address2 = result_from_query['address2']
		self.city = result_from_query['city']
		self.state = result_from_query['state']
		self.zip = result_from_query['zip']
		self.category = category
		self.has_extra_content = False
		self.getExtraContent()

	def getExtraContent(self):
		if not self.has_extra_content:
			self._enrichWithUrlContent()
			self.has_extra_content = True
	
	def _enrichWithUrlContent(self):
		num_pages = self.review_count / 40
	
		self.reviews = []
		for page in range(0, self.review_count, 40):			
			page = get_page('{}?start={}'.format(self.url, page))
			
			if not hasattr(self, 'price_range'):
				matches = re.search(YelpBusiness.PRICE_RANGE_RE, page, re.DOTALL)
				if matches:
					self.price_range = matches.group(1)
						
			ratings = re.findall(YelpBusiness.REVIEW_RATINGS_RE, page, re.DOTALL)		
			if ratings:		
				pub_dates = re.findall(YelpBusiness.REVIEW_PUBLISHED_RE, page, re.DOTALL)
				if pub_dates:
					for rating, pub_date in zip(ratings, pub_dates):
						review = YelpReview(rating, datetime.strptime(pub_date, '%Y-%m-%d'))
						self.reviews.append(review)
						
	def filter_reviews_by_date(self, start_dt, end_dt):
		filtered_reviews = []
		for review in self.reviews:
			if review.pub_date.date() >= start_dt and review.pub_date.date() <= end_dt:
				filtered_reviews.append(review)
		self.reviews_exluded = (len(self.reviews) != len(filtered_reviews))
		self.reviews = filtered_reviews
		
	def get_address(self):
		return '{}, {}, {}, {} {}'.format(self.address1, self.address2, self.city, self.state, self.zip).replace(' ', '+')
	
	def __str__(self):
		out = 'Business Name: {}\n' \
			'URL: {}\n' \
			'Zip: {}\n' \
			'Latitude: {}\n' \
			'Longitude: {}\n' \
			'Avg Rating: {}\n' \
			'# Reviews: {}\n'.format(self.name, self.url, self.zip, self.latitude, self.longitude, self.avg_rating, self.review_count)			

		if hasattr(self, 'price_range'):
			out += 'Price Range: {}\n'.format(self.price_range)
		
		if hasattr(self, 'reviews'):
			out += '# Collected Reviews: {}\n'.format(len(self.reviews))
			
		return out
	
	def __repr_(self):
		return self.__str__()

class YelpReview():
	def __init__(self, rating, pub_date):
		self.rating = rating
		self.pub_date = pub_date
	
	def __str__(self):
		return '{} = {}'.format(self.pub_date, self.rating)
		
	def __repr__(self):
		return self.__str__()