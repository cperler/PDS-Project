import urllib2
import json
import re
import sys

#pass in origin, test address, and desired radius to see if the test address is within that radius
#returns false if the test address isn't in the desired radius, and true if it is
#could also pass in latitude or longitude

origin = '158+east+7th+st.+nyc'
test_place = '44+West+4th+Street+nyc'

def test_radius(origin,test,distance):
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
			
	
print test_radius(origin, test_place, 300)
