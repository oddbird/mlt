import json

from django.test import TestCase
from django.test.client import RequestFactory

from .utils import create_parcel, create_mpolygon



__all__ = ["GeoJSONViewTest"]



class GeoJSONViewTest(TestCase):
    @property
    def view(self):
        from mlt.map.views import geojson
        return geojson


    def test_content_type(self):
        req = RequestFactory().get("/map/geojson/")

        response = self.view(req, "0.0", "3.0", "4.0", "7.0")

        self.assertEqual(response["content-type"], "application/json")


    def test_contains(self):
        create_parcel(
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (1.0, 5.0)]))
        create_parcel(
            geom=create_mpolygon(
                [(1.0, 8.0), (1.0, 9.0), (2.0, 9.0), (1.0, 8.0)]))

        req = RequestFactory().get("/map/geojson/")

        response = self.view(req, "0.0", "3.0", "4.0", "5.5")

        self.assertEqual(
            json.loads(response.content),
            {
                "crs": None,
                "type": "FeatureCollection",
                "features": [
                    {
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": [[[
                                        [1.0, 5.0],
                                        [1.0, 6.0],
                                        [2.0, 6.0],
                                        [1.0, 5.0]
                                        ]]]
                            },
                        "type": "Feature",
                        "id": 1,
                        "properties": {
                            "first_owner": "Van Gordon",
                            "classcode": "Single Family Residence",
                            "pl": "111 22",
                            "address": "3635 Van Gordon St"
                            }
                        }
                    ]
                }
            )
