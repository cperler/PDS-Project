from googlemaps import GoogleMaps

#latitude & longitude

address_entry = raw_input('Enter an address ')
gmaps = GoogleMaps('AIzaSyC2LVa5tMpQmnYw3VSxfwlPvME5SXdCPsU')
address = '%s' %address_entry
lat, lng = gmaps.address_to_latlng(address)
print "The latitude and longitude for that address is %f, %f" %(lat, lng)
