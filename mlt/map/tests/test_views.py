import json

from django.core.urlresolvers import reverse

from django_webtest import WebTest

from .utils import create_parcel, create_mpolygon



__all__ = ["GeoJSONViewTest", "AddAddressViewTest"]



class AuthenticatedWebTest(WebTest):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            "provplan", "provplan@example.com", "sekritplans")



class AddAddressViewTest(AuthenticatedWebTest):
    @property
    def url(self):
        return reverse("map_add_address")


    def test_get_form(self):
        response = self.app.get(self.url, user=self.user)

        self.assertEqual(
            sorted(response.form.fields.keys()),
            [
                None, # submit button has no name
                "city",
                "complex_name",
                "csrfmiddlewaretoken",
                "multi_units",
                "notes",
                "state",
                "street_name",
                "street_number",
                "street_suffix",
                ]
            )


    def test_post(self):
        response = self.app.get(self.url, user=self.user)
        form = response.form
        form["city"] = "Providence"
        form["state"] = "RI"
        form["street_number"] = "3635"
        form["street_name"] = "Van Gordon",
        form["street_suffix"] = "St"

        response = form.submit()

        self.assertEqual(response.status_int, 200)
        from mlt.map.models import Address
        self.assertEqual(Address.objects.count(), 1, response.body)



class GeoJSONViewTest(AuthenticatedWebTest):
    def get(self, **kwargs):
        return self.app.get(
            reverse("map_geojson", kwargs=kwargs), user=self.user)


    def test_login_required(self):
        response = self.app.get(
            reverse(
                "map_geojson", kwargs=dict(
                    westlat="0.0",
                    eastlat="3.0",
                    southlng="4.0",
                    northlng="7.0",
                    )))

        self.assertEqual(response.status_int, 302)
        self.assertEqual(
            response.headers["location"],
            "http://localhost:80/account/login/"
            "?next=/map/geojson/0.0/3.0/4.0/7.0/")


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
