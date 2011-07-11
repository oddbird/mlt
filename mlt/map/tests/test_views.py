import json
import urllib

from django.core.urlresolvers import reverse

from django_webtest import WebTest

from .utils import create_address, create_parcel, create_mpolygon, create_user



__all__ = [
    "ImportViewTest",
    "AssociateViewTest",
    "AddressesViewTest",
    "GeoJSONViewTest",
    "AddAddressViewTest"
    ]



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



class AssociateViewTest(AuthenticatedWebTest):
    url_name = "map_associate"


    def setUp(self):
        super(AssociateViewTest, self).setUp()

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
            extra_environ={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"})


    def test_associate_one(self):
        create_parcel(pl="1234")
        a = create_address()

        res = self.post(self.url, {"pl": "1234", "aid": a.id})

        self.assertEqual(a.__class__.objects.get(id=a.id).pl, "1234")
        self.assertEqual(
            json.loads(res.body),
            {
                "pl": "1234",
                "addresses": [
                    {"id": a.id, "needs_review": True}
                    ],
                "messages": []
             })


    def test_associate_multiple(self):
        create_parcel(pl="1234")
        a1 = create_address()
        a2 = create_address()

        res = self.post(self.url, {"pl": "1234", "aid": [a1.id, a2.id]})

        self.assertEqual(a1.__class__.objects.get(id=a1.id).pl, "1234")
        self.assertEqual(a2.__class__.objects.get(id=a2.id).pl, "1234")
        self.assertEqual(
            json.loads(res.body),
            {
                "pl": "1234",
                "addresses": [
                    {"id": a1.id, "needs_review": True},
                    {"id": a2.id, "needs_review": True}
                    ],
                "messages": []
             })


    def test_no_such_parcel(self):
        a = create_address()

        res = self.post(self.url, {"pl": "1234", "aid": a.id})

        self.assertEqual(a.__class__.objects.get(id=a.id).pl, "")
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

        self.assertEqual(a.__class__.objects.get(id=a.id).pl, "")
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

        res = self.post(self.url, {"pl": "1234"})

        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No addresses with given IDs ()"
                        }
                    ]
                }
            )


    def test_no_such_addresses(self):
        create_parcel(pl="1234")

        res = self.post(self.url, {"pl": "1234", "aid": "123"})

        self.assertEqual(
            json.loads(res.body),
            {
                "messages": [
                    {
                        "level": 40,
                        "tags": "error",
                        "message": "No addresses with given IDs (123)"
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

        self.assertEqual(
            [a["index"] for a in res.json["addresses"]], range(1, 21))


    def test_get_specific_addresses(self):
        for i in range(50):
            create_address(street_number=str(i+1))

        res = self.app.get(
            self.url + "?start=%s&num=%s" % (21, 10),
            user=self.user)

        self.assertEqual(
            [a["index"] for a in res.json["addresses"]], range(21, 31))



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
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (1.0, 5.0)]))
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
                                        [1.0, 5.0]
                                        ]]]
                            },
                        u"type": u"Feature",
                        u"id": p.id,
                        u"properties": {
                            u"first_owner": u"Van Gordon",
                            u"classcode": u"Single Family Residence",
                            u"pl": u"111 22",
                            u"address": u"3635 Van Gordon St",
                            u"mapped": False,
                            u"mapped_to": []
                            }
                        }
                    ]
                }
            )
