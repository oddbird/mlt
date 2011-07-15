"""
Modified version of geopy's GeocoderDotUS geocoder that returns dictionary of
fully-parsed address data rather than recombining into a single string, and
always returns first match found (or None).

"""
import csv
from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.dot_us import GeocoderDotUS



def update(address, data):
    address.street_prefix = data["prefix"]
    address.street_number = data["number"]
    address.street_name = data["street"]
    address.street_type = data["type"]
    address.street_suffix = data["suffix"]
    address.city = data["city"]
    address.state = data["state"]



def prep(address):
    return ", ".join([address.street, address.city, address.state])



def geocode(prepped_address):
    return g.geocode(prepped_address)



class GeocoderDotUSParsed(GeocoderDotUS):
    def geocode(self, query):
        query_str = self.format_string % query

        page = urlopen("%s?%s" % (
            self.get_url(),
            urlencode({'address':query_str})
        ))

        reader = csv.reader(page)

        for place in reader:
            parsed = self._parse_result(place)
            if parsed is not None:
                return parsed

        return None


    @staticmethod
    def _parse_result(result):
        # turn x=y pairs ("lat=47.6", "long=-117.426") into dict key/value pairs:
        place = dict(
            filter(lambda x: len(x)>1, # strip off bits that aren't pairs (i.e. "geocoder modified" status string")
            map(lambda x: x.split('=', 1), result) # split the key=val strings into (key, val) tuples
        ))

        if not "lat" in place:
            return None

        return place



g = GeocoderDotUSParsed()
