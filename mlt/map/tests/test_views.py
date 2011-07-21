import datetime
import json
import urllib

from django.core.urlresolvers import reverse
from django.utils.formats import date_format

from django_webtest import WebTest

from mock import patch

from .utils import create_address, create_parcel, create_mpolygon, create_user



__all__ = [
    "ImportViewTest",
    "AssociateViewTest",
    "AddressesViewTest",
    "GeoJSONViewTest",
    "AddAddressViewTest",
    "FilterAutocompleteViewTest",
    "GeocodeViewTest",
    "AddressActionsViewTest",
    ]



def refresh(obj):
    return obj.__class__._base_manager.get(pk=obj.pk)


class AuthenticatedWebTest(WebTest):
    url_name = None


    def setUp(self):
        self.user = create_user()


    @property
    def url(self):
        return reverse(self.url_name)


    def test_login_required(self):
        # clear any previous logged-in session
        self.app.reset()

        response = self.app.get(self.url)

        self.assertEqual(response.status_int, 302)


class ImportViewTest(AuthenticatedWebTest):
    url_name = "map_import_addresses"


    def test_get_form_ajax(self):
        res = self.app.get(
            self.url, user=self.user,
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"})

        self.assertTrue("html" in res.json)
        self.assertTrue("multipart/form-data" in res.json["html"])
        self.assertEqual(res.templates[0].name, "import/_form.html")


    def test_post_form_with_form_errors(self):
        res = self.app.get(
            self.url, user=self.user)

        res = res.forms["import-address-form"].submit()

        self.assertEqual(
            [u.li.text for u in res.html.findAll("ul", "errorlist")],
            ["This field is required.", "This field is required."])


    def test_post_form_with_import_errors(self):
        res = self.app.get(
            self.url, user=self.user)

        form = res.forms["import-address-form"]
        form["source"] = "mysource"
        form["file"] = ("bad.csv", "Bad, Address, Yo")

        res = form.submit()

        self.assertEqual(
            res.html.findAll("ul", "errorlist")[0].li.text,
            "Value &#39;YO&#39; is not a valid choice.")


    def test_post_form_with_success(self):
        res = self.app.get(
            self.url, user=self.user)

        form = res.forms["import-address-form"]
        form["source"] = "mysource"
        form["file"] = ("good.csv", "123 Good St, Providence, RI")

        res = form.submit().follow()

        self.assertEqual(
            res.html.findAll("li", "success")[0].p.text,
            "Successfully imported 1 addresses (0 duplicates).")



class CSRFAuthenticatedWebTest(AuthenticatedWebTest):
    url_name = "map_associate"


    def setUp(self):
        super(CSRFAuthenticatedWebTest, self).setUp()

        res = self.app.get("/", user=self.user)
        self.csrftoken = dict(
            [i.strip() for i in c.split(";")[0].split("=")]
            for c in res.headers.getall("set-cookie")
            )["csrftoken"]


    def post(self, url, data):
        data["csrfmiddlewaretoken"] = self.csrftoken
        return self.app.post(
            url,
            urllib.urlencode(data, doseq=True),
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)



class AssociateViewTest(CSRFAuthenticatedWebTest):
    url_name = "map_associate"


    def setUp(self):
        super(AssociateViewTest, self).setUp()

        res = self.app.get("/", user=self.user)
        self.csrftoken = dict(
            [i.strip() for i in c.split(";")[0].split("=")]
            for c in res.headers.getall("set-cookie")
            )["csrftoken"]


    def post(self, url, data, user=None):
        data["csrfmiddlewaretoken"] = self.csrftoken
        return self.app.post(
            url,
            urllib.urlencode(data, doseq=True),
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=user or self.user)


    def test_associate_one(self):
        from mlt.dt import utc_to_local

        create_parcel(pl="1234")
        a = create_address()

        res = self.post(self.url, {"maptopl": "1234", "aid": a.id})

        a = refresh(a)
        self.assertEqual(a.pl, "1234")
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 1)
        addy = res.json["mapped_to"][0]
        self.assertEqual(addy["id"], a.id)
        self.assertEqual(addy["mapped_by"], self.user.username)
        self.assertEqual(addy["mapped_timestamp"], date_format(
                utc_to_local(a.mapped_timestamp), "DATETIME_FORMAT"))
        self.assertEqual(addy["needs_review"], True)


    def test_associate_trusted(self):
        from django.contrib.auth.models import Permission

        create_parcel(pl="1234")
        a = create_address()
        u = create_user()
        p = Permission.objects.get_by_natural_key(
            "mappings_trusted",
            "map",
            "address")
        u.user_permissions.add(p)

        res = self.post(self.url, {"maptopl": "1234", "aid": a.id}, user=u)

        a = refresh(a)
        self.assertEqual(a.pl, "1234")
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 1)
        addy = res.json["mapped_to"][0]
        self.assertEqual(addy["id"], a.id)
        self.assertEqual(addy["mapped_by"], u.username)
        self.assertEqual(addy["needs_review"], False)


    def test_associate_another(self):
        from mlt.dt import utc_to_local

        create_parcel(pl="1234")
        create_address(pl="1234")
        a2 = create_address()

        res = self.post(self.url, {"maptopl": "1234", "aid": a2.id})

        a2 = refresh(a2)
        self.assertEqual(a2.pl, "1234")
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 2)
        addy = [a for a in res.json["mapped_to"] if a["id"] == a2.id][0]
        self.assertEqual(addy["id"], a2.id)
        self.assertEqual(addy["mapped_by"], self.user.username)
        self.assertEqual(addy["mapped_timestamp"], date_format(
                utc_to_local(a2.mapped_timestamp), "DATETIME_FORMAT"))
        self.assertEqual(addy["needs_review"], True)


    def test_associate_multiple(self):
        from mlt.dt import utc_to_local

        create_parcel(pl="1234")
        a1 = create_address()
        a2 = create_address()

        res = self.post(self.url, {"maptopl": "1234", "aid": [a1.id, a2.id]})

        a1 = refresh(a1)
        a2 = refresh(a2)
        self.assertEqual(a1.pl, "1234")
        self.assertEqual(a2.pl, "1234")
        self.assertEqual(res.json["pl"], "1234")
        mt = res.json["mapped_to"]
        self.assertEqual(len(mt), 2)
        self.assertEqual(set([a["id"] for a in mt]), set([a1.id, a2.id]))
        self.assertEqual(
            set([a["mapped_by"] for a in mt]), set([self.user.username])
            )
        self.assertEqual(
            set([a["mapped_timestamp"] for a in mt]),
            set([date_format(utc_to_local(a1.mapped_timestamp),
                             "DATETIME_FORMAT")])
            )
        self.assertTrue(all([a["needs_review"] for a in mt]))


    def test_associate_by_filter(self):
        from mlt.dt import utc_to_local

        create_parcel(pl="1234")
        a1 = create_address(city="Providence")
        a2 = create_address(city="Providence")
        a3 = create_address(city="Pawtucket")

        res = self.post(self.url, {"maptopl": "1234", "city": "Providence"})

        a1 = refresh(a1)
        a2 = refresh(a2)
        a3 = refresh(a3)
        self.assertEqual(a1.pl, "1234")
        self.assertEqual(a2.pl, "1234")
        self.assertEqual(a3.pl, "")
        self.assertEqual(res.json["pl"], "1234")
        mt = res.json["mapped_to"]
        self.assertEqual(len(mt), 2)
        self.assertEqual(set([a["id"] for a in mt]), set([a1.id, a2.id]))
        self.assertEqual(
            set([a["mapped_by"] for a in mt]), set([self.user.username])
            )
        self.assertEqual(
            set([a["mapped_timestamp"] for a in mt]),
            set([date_format(utc_to_local(a1.mapped_timestamp),
                             "DATETIME_FORMAT")])
            )
        self.assertTrue(all([a["needs_review"] for a in mt]))


    def test_associate_by_filter_unmapped(self):
        create_parcel(pl="1234")
        create_address(city="Providence")
        create_address(city="Providence")
        create_address(city="Pawtucket")

        res = self.post(
            self.url,
            {"maptopl": "1234", "city": "Providence", "status": "unmapped"})

        self.assertEqual(
            res.json["messages"],
            [
                {
                    "level": 25,
                    "message": "Mapped 2 addresses to PL 1234",
                    "tags": "success"
                    }
                ]
            )


    def test_no_such_parcel(self):
        a = create_address()

        res = self.post(self.url, {"maptopl": "1234", "aid": a.id})

        self.assertEqual(refresh(a).pl, "")
        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No parcel with PL '1234'"
                        }
                    ]
                }
            )


    def test_no_pl(self):
        a = create_address()

        res = self.post(self.url, {"aid": a.id})

        self.assertEqual(refresh(a).pl, "")
        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No PL provided."
                        }
                    ]
                }
            )


    def test_no_addresses(self):
        create_parcel(pl="1234")

        res = self.post(self.url, {"maptopl": "1234"})

        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No addresses selected."
                        }
                    ]
                }
            )


    def test_no_such_addresses(self):
        create_parcel(pl="1234")

        res = self.post(self.url, {"maptopl": "1234", "aid": "123"})

        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No addresses selected."
                        }
                    ]
                }
            )



class AddressesViewTest(AuthenticatedWebTest):
    url_name = "map_addresses"


    def test_get_addresses(self):
        for i in range(50):
            create_address(street_number=str(i+1))

        res = self.app.get(self.url, user=self.user)

        from mlt.map.utils import letter_key

        self.assertEqual(
            [a["index"] for a in res.json["addresses"]],
            [letter_key(i) for i in range(1, 21)])


    def test_get_specific_addresses(self):
        for i in range(50):
            create_address(street_number=str(i+1))

        res = self.app.get(
            self.url + "?start=%s&num=%s" % (21, 10),
            user=self.user)

        from mlt.map.utils import letter_key

        self.assertEqual(
            [a["index"] for a in res.json["addresses"]],
            [letter_key(i) for i in range(21, 31)])


    def test_sort(self):
        a1 = create_address(
            input_street="123 N Main St",
            city="Providence",
            import_timestamp=datetime.datetime(2011, 7, 15, 1, 2, 3))
        a2 = create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            import_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))
        a3 = create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            import_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))

        res = self.app.get(
            self.url + "?sort=city&sort=-street&sort=import_timestamp",
            user=self.user)

        self.assertEqual(
            [a["id"] for a in res.json["addresses"]],
            [a2.id, a3.id, a1.id]
            )


    def test_sort_bad_field(self):
        res = self.app.get(
            self.url + "?sort=city&sort=bad",
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)

        self.assertEqual(
            res.json["messages"],
            [
                {
                    "message": "'bad' is not a valid sort field.",
                    "level": 40,
                    "tags": "error"
                    }
                ]
            )


    def assertAddresses(self, response, ids):
        self.assertEqual(
            set([a["id"] for a in response.json["addresses"]]),
            set(ids)
            )


    def test_filter(self):
        a1 = create_address(
            city="Providence",
            )
        create_address(
            city="Albuquerque",
            )
        create_address(
            city="Albuquerque",
            )

        res = self.app.get(
            self.url + "?city=Providence",
            user=self.user)

        self.assertAddresses(res, [a1.id])


    def test_filter_by_not_ids(self):
        create_address(
            city="Providence",
            )
        a2 = create_address(
            city="Albuquerque",
            )
        a3 = create_address(
            city="Albuquerque",
            )

        res = self.app.get(
            self.url + "?city=Albuquerque&notid=%s" % a2.id,
            user=self.user)

        self.assertAddresses(res, [a3.id])


    def test_filter_multiple_same_field(self):
        a1 = create_address(
            city="Providence",
            )
        a2 = create_address(
            city="Albuquerque",
            )
        create_address(
            city="Rapid City",
            )

        res = self.app.get(
            self.url + "?city=Providence&city=Albuquerque",
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id])


    def test_filter_multiple(self):
        a1 = create_address(
            state="RI",
            city="Providence",
            )
        create_address(
            state="NM",
            city="Providence",
            )
        create_address(
            state="RI",
            city="Pawtucket",
            )

        res = self.app.get(
            self.url + "?city=Providence&state=RI",
            user=self.user)

        self.assertAddresses(res, [a1.id])


    def test_filter_user(self):
        u1 = create_user()
        u2 = create_user()
        a1 = create_address(
            imported_by=u1,
            )
        a2 = create_address(
            imported_by=u1,
            )
        create_address(
            imported_by=u2
            )

        res = self.app.get(
            self.url + "?imported_by=%s" % u1.id,
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id])


    def test_status_filter_unmapped(self):
        create_address(pl="123", needs_review=True)
        create_address(pl="345", needs_review=False)
        a3 = create_address(pl="", needs_review=True)
        a4 = create_address(pl="", needs_review=False)


        res = self.app.get(
            self.url + "?status=unmapped",
            user=self.user)

        self.assertAddresses(res, [a3.id, a4.id])


    def test_status_filter_flagged(self):
        a1 = create_address(pl="123", needs_review=True)
        create_address(pl="345", needs_review=False)
        create_address(pl="", needs_review=True)
        create_address(pl="", needs_review=False)


        res = self.app.get(
            self.url + "?status=flagged",
            user=self.user)

        self.assertEqual(
            [a["id"] for a in res.json["addresses"]],
            [a1.id] # not a3 because it is unmapped
            )


    def test_status_filter_approved(self):
        create_address(pl="123", needs_review=True)
        a2 = create_address(pl="345", needs_review=False)
        create_address(pl="", needs_review=True)
        create_address(pl="", needs_review=False)


        res = self.app.get(
            self.url + "?status=approved",
            user=self.user)

        self.assertAddresses(res, [a2.id])


    def test_count(self):
        create_address(
            input_street="123 N Main St",
            city="Providence",
            import_timestamp=datetime.datetime(2011, 7, 15, 1, 2, 3))
        create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            import_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))
        create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            import_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))

        res = self.app.get(self.url + "?city=Albuquerque&num=1&count=true", user=self.user)

        self.assertEqual(res.json["count"], 2)
        self.assertEqual(len(res.json["addresses"]), 1)




class AddAddressViewTest(AuthenticatedWebTest):
    url_name = "map_add_address"


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
                "street_type",
                ]
            )


    def test_post(self):
        response = self.app.get(self.url, user=self.user)
        form = response.form
        form["city"] = "Providence"
        form["state"] = "RI"
        form["street_number"] = "3635"
        form["street_name"] = "Van Gordon",
        form["street_type"] = "St"

        response = form.submit()

        self.assertEqual(response.status_int, 200)
        from mlt.map.models import Address
        self.assertEqual(Address.objects.count(), 1, response.body)



class GeoJSONViewTest(AuthenticatedWebTest):
    url_name = "map_geojson"


    def get(self, **kwargs):
        return self.app.get(
            self.url + "?" + urllib.urlencode(kwargs),
            user=self.user)


    def test_content_type(self):
        response = self.get(
            westlng="0.0", eastlng="3.0", southlat="4.0", northlat="7.0")

        self.assertEqual(response.headers["content-type"], "application/json")


    def test_incomplete_input(self):
        response = self.get(
            westlng="0.0", eastlng="3.0", southlat="4.0")

        self.assertEqual(json.loads(response.body), {})


    def test_contains(self):
        self.maxDiff = None
        p = create_parcel(
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (2.0, 5.0), (1.0, 5.0)]))
        create_parcel(
            geom=create_mpolygon(
                [(1.0, 8.0), (1.0, 9.0), (2.0, 9.0), (1.0, 8.0)]))

        response = self.get(
            westlng="0.0", eastlng="3.0", southlat="4.0", northlat="5.5")

        self.assertEqual(
            json.loads(response.body),
            {
                u"crs": None,
                u"type": u"FeatureCollection",
                u"features": [
                    {
                        u"geometry": {
                            u"type": u"MultiPolygon",
                            u"coordinates": [[[
                                        [1.0, 5.0],
                                        [1.0, 6.0],
                                        [2.0, 6.0],
                                        [2.0, 5.0],
                                        [1.0, 5.0],
                                        ]]]
                            },
                        u"type": u"Feature",
                        u"id": int(p.id),
                        u"properties": {
                            u"latitude": 5.5,
                            u"longitude": 1.5,
                            u"first_owner": u"Van Gordon",
                            u"classcode": u"Single Family Residence",
                            u"pl": u"111 22",
                            u"address": u"3635 Van Gordon St",
                            u"mapped": False,
                            u"mapped_to": [],
                            u"latitude": 5.5,
                            u"longitude": 1.5,
                            }
                        }
                    ]
                }
            )



class FilterAutocompleteViewTest(AuthenticatedWebTest):
    url_name = "map_filter_autocomplete"


    def test_filter(self):
        blametern = create_user(username="blametern")
        create_address(
            input_street="123 N Main St",
            city="Providence",
            imported_by=blametern)
        create_address(
            input_street="456 N Main St",
            city="Albuquerque")
        create_address(
            input_street="123 N Main St",
            city="Albuquerque")

        res = self.app.get(self.url + "?q=alb", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{
                    "desc": "city",
                    "field": "city",
                    "value": "Albuquerque",
                    "q": "alb",
                    "rest": "uquerque",
                    }]
            )

        res = self.app.get(self.url + "?q=b", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{      "q": "b",
                    "field": "imported_by",
                    "value": blametern.id,
                    "rest": "lametern",
                    "desc": "imported by"
                    }]
            )


    def test_no_filter(self):
        res = self.app.get(
            self.url,
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)

        self.assertEqual(
            res.json["messages"],
            [{
                    "message": "Filter autocomplete requires 'q' parameter.",
                    "level": 40,
                    "tags": "error"
                    }]
            )



class GeocodeViewTest(AuthenticatedWebTest):
    url_name = "map_geocode"

    @patch("mlt.map.geocoder.geocode")
    def test_geocode(self, geocode):
        self.maxDiff = None
        geocode.return_value = {
            "city": "Providence",
            "lat": "41.823991",
            "long": "-71.406619",
            "number": "123",
            "prefix": "S",
            "state": "RI",
            "street": "Main",
            "suffix": "",
            "type": "St",
            "zip": "02903"
            }

        a = create_address(
            city="Providence",
            input_street="123 S Main St",
            state="RI",
            street_number="",
            street_name="",
            street_prefix="",
            street_suffix="",
            street_type="",
            )

        res = self.app.get(self.url + "?id=%s" % a.id , user=self.user)

        a = refresh(a)

        self.assertEqual(a.street_number, "123")
        self.assertEqual(a.street_prefix, "S")
        self.assertEqual(a.street_name, "Main")
        self.assertEqual(a.street_type, "St")

        self.assertEqual(
            res.json,
            {
                "address": {
                    "city": "Providence",
                    "complex_name": "",
                    "id": a.id,
                    "import_source": "test-created",
                    "import_timestamp": "June 15, 2011 at 4:14 a.m.",
                    "imported_by": a.imported_by.username,
                    "mapped_by": None,
                    "mapped_timestamp": None,
                    "multi_units": False,
                    "needs_review": False,
                    "notes": "",
                    "pl": "",
                    "state": "RI",
                    "street": "123 S Main St",
                    "street_name": "Main",
                    "street_number": "123",
                    "street_prefix": "S",
                    "street_suffix": "",
                    "street_type": "St",
                    "latitude": 41.823991,
                    "longitude": -71.406619,
                    }
                }
            )

        geocode.assert_called_with("123 S Main St, Providence, RI")


    def test_geocode_no_id(self):
        res = self.app.get(
            self.url,
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)

        self.assertEqual(
            res.json["messages"],
            [
                {
                    "message": "Geocoding requires an address 'id' parameter.",
                    "level": 40,
                    "tags": "error"
                    }
                ])


    def test_geocode_bad_id(self):
        res = self.app.get(
            self.url + "?id=2100",
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)

        self.assertEqual(
            res.json["messages"],
            [
                {
                    "message": "Geocoding: '2100' is not a valid address ID.",
                    "level": 40,
                    "tags": "error"
                    }
                ])


    @patch("mlt.map.geocoder.geocode")
    def test_cant_geocode(self, geocode):
        geocode.return_value = None

        a = create_address(
            city="Providence",
            input_street="123 S Main St",
            state="RI",
            street_number="",
            street_name="",
            street_prefix="",
            street_suffix="",
            street_type="",
            )

        res = self.app.get(
            self.url + "?id=%s" % a.id ,
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
            user=self.user)

        self.assertEqual(
            res.json["messages"],
            [
                {
                    'level': 20,
                    'message':
                        "Unable to geocode '123 S Main St, Providence, RI'.",
                    'tags': 'info'
              }
             ]
            )

        geocode.assert_called_with("123 S Main St, Providence, RI")



class AddressActionsViewTest(CSRFAuthenticatedWebTest):
    url_name = "map_address_actions"


    def test_delete(self):
        a1 = create_address()
        a2 = create_address()

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id], "action": "delete"},
            )

        self.assertEqual(
            res.json,
            {
                'messages': [{
                        'level': 25,
                        'message': '2 addresses deleted.',
                        'tags': 'success'
                        }],
                "success": True
                }
            )

        self.assertEqual(a1.__class__.objects.count(), 0)


    def test_delete_by_filter(self):
        a1 = create_address(city="Providence")
        a2 = create_address(city="Pawtucket")

        res = self.post(
            self.url,
            {"action": "delete", "city": "Providence"},
            )

        self.assertEqual(
            res.json,
            {
                'messages': [{
                        'level': 25,
                        'message': '1 address deleted.',
                        'tags': 'success'
                        }],
                "success": True
                }
            )

        self.assertEqual(a1.__class__.objects.count(), 1)


    def test_approve(self):
        a1 = create_address(pl="", needs_review=True)
        a2 = create_address(pl="123", needs_review=True)
        a3 = create_address(pl="234", needs_review=False)

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id, a3.id], "action": "approve"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "1 mapping approved.",
                    "tags": "success",
                    }],
            )
        self.assertTrue(res.json["success"])
        self.assertEqual(len(res.json["addresses"]), 1)

        a2 = refresh(a2)
        self.assertEqual(a2.needs_review, False)


    def test_approve_by_filter(self):
        a1 = create_address(city="Providence", pl="123", needs_review=True)
        a2 = create_address(city="Pawtucket", pl="123", needs_review=True)
        create_address(city="Providence", pl="123", needs_review=False)
        create_address(city="Providence", pl="")

        res = self.post(
            self.url,
            {"action": "approve", "city": "Providence"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "1 mapping approved.",
                    "tags": "success",
                    }],
            )
        self.assertTrue(res.json["success"])
        self.assertEqual(len(res.json["addresses"]), 1)

        a1 = refresh(a1)
        self.assertEqual(a1.needs_review, False)

        a2 = refresh(a2)
        self.assertEqual(a2.needs_review, True)


    def test_flag(self):
        a1 = create_address(pl="", needs_review=False)
        a2 = create_address(pl="123", needs_review=True)
        a3 = create_address(pl="234", needs_review=False)

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id, a3.id], "action": "flag"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "1 mapping flagged.",
                    "tags": "success",
                    }],
            )
        self.assertTrue(res.json["success"])
        self.assertEqual(len(res.json["addresses"]), 1)

        a3 = refresh(a3)
        self.assertEqual(a3.needs_review, True)


    def test_flag_by_filter(self):
        a1 = create_address(pl="123", needs_review=False, city="Providence")
        a2 = create_address(pl="234", needs_review=False, city="Pawtucket")
        create_address(pl="123", needs_review=True, city="Providence")
        create_address(pl="", needs_review=False, city="Providence")

        res = self.post(
            self.url,
            {"action": "flag", "city": "Providence"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "1 mapping flagged.",
                    "tags": "success",
                    }],
            )
        self.assertTrue(res.json["success"])
        self.assertEqual(len(res.json["addresses"]), 1)

        self.assertEqual(refresh(a1).needs_review, True)
        self.assertEqual(refresh(a2).needs_review, False)


    def test_no_ids(self):
        res = self.post(self.url, {})

        self.assertEqual(
            res.json,
            {"messages": [{"level": 40,
                           "message": "No addresses selected.",
                           "tags": "error"}],
             "success": False}
            )


    def test_bad_ids(self):
        res = self.post(self.url, {"aid": [1001]})

        self.assertEqual(
            res.json,
            {"messages": [{"level": 40,
                           "message": "No addresses selected.",
                           "tags": "error"}],
             "success": False}
            )


    def test_bad_action(self):
        a1 = create_address()

        res = self.post(self.url, {"aid": [a1.id], "action": "bad"})

        self.assertEqual(
            res.json,
            {"messages": [{"level": 40,
                           "message": "Unknown action 'bad'",
                           "tags": "error"}],
             "success": False}
            )
