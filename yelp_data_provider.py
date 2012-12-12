from yelp import ReviewSearchApi
from utils import *

YELP_KEY = '-zHKh7Z8UaWOSNECS85GWA'

class YelpDataProvider():	
	def __init__(self, APIKEY):
		self.APIKEY = APIKEY
		
	def getReviewsByLocation(self, location, radius=1, search_terms='', limit=20):
		filename = '{}_{}_{}_reviews.txt'.format(location, search_terms, limit)
		if file_exists(filename):
			print 'Loading {} reviews for {} - {} from file {}.'.format(limit, location, search_terms, filename)
			return pickle_load(filename)
		
		results = ReviewSearchApi(client_key=self.APIKEY, output='json').by_location(location, term=search_terms, radius=radius, num_biz_requested=limit)
		if results['message']['text'] != 'OK':
			raise Exception('Error retrieving Yelp results.')
			
		businesses = []
		for result in results['businesses']:
			business = YelpBusiness(result)
			businesses.append(business)
		pickle_it(filename, businesses)
		return businesses
		
class YelpBusiness():
	PRICE_RANGE_RE = 'Ultra High-End\">(.*?)<'
	REVIEW_RATINGS_RE = 'ratingValue\" content\=\"(.*?)\"'
	REVIEW_PUBLISHED_RE = 'datePublished\" content\=\"(.*?)\"'
	
	def __init__(self, result_from_query):
		self.id = result_from_query['id']
		self.name = result_from_query['name']
		self.url = result_from_query['url']
		self.latitude = result_from_query['latitude']
		self.longitude = result_from_query['longitude']
		self.avg_rating = result_from_query['avg_rating']
		self.review_count = result_from_query['review_count']
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
						review = YelpReview(rating, pub_date)
						self.reviews.append(review)
	
	def __str__(self):
		out = 'Business Name: {}\n' \
			'URL: {}\n' \
			'Latitude: {}\n' \
			'Longitude: {}\n' \
			'Avg Rating: {}\n' \
			'# Reviews: {}\n'.format(self.name, self.url, self.latitude, self.longitude, self.avg_rating, self.review_count)			

		if hasattr(self, 'price_range'):
			out += 'Price Range: {}\n'.format(self.price_range)
		
		if hasattr(self, 'reviews'):
			out += '# Collected Reviews: {}\n'.format(len(self.reviews))
			
		return out

class YelpReview():
	def __init__(self, rating, pub_date):
		self.rating = rating
		self.pub_date = pub_date