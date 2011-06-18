import json

from django.core.urlresolvers import reverse

from django_webtest import WebTest

from .utils import create_parcel, create_mpolygon



__all__ = ["GeoJSONViewTest"]



class GeoJSONViewTest(WebTest):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            "provplan", "provplan@example.com", "sekritplans")


    def get(self, **kwargs):
        return self.app.get(
            reverse("map_geojson", kwargs=kwargs), user=self.user)


    def test_content_type(self):
        response = self.get(
            westlat="0.0", eastlat="3.0", southlng="4.0", northlng="7.0")

        self.assertEqual(response.headers["content-type"], "application/json")


    def test_contains(self):
        create_parcel(
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (1.0, 5.0)]))
        create_parcel(
            geom=create_mpolygon(
                [(1.0, 8.0), (1.0, 9.0), (2.0, 9.0), (1.0, 8.0)]))

        response = self.get(
            westlat="0.0", eastlat="3.0", southlng="4.0", northlng="5.5")

        self.assertEqual(
            json.loads(response.body),
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
