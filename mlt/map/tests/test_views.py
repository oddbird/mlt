import datetime
import json
import urllib

from django.core.urlresolvers import reverse
from django.utils.formats import date_format

from django_webtest import WebTest

from mock import patch

from .utils import (
    create_address, create_parcel, create_mpolygon, create_user,
    create_address_batch, refresh, zip_shapefile)



__all__ = [
    "ImportViewTest",
    "ExportViewTest",
    "AssociateViewTest",
    "AddressesViewTest",
    "HistoryViewTest",
    "GeoJSONViewTest",
    "AddAddressViewTest",
    "EditAddressViewTest",
    "FilterAutocompleteViewTest",
    "HistoryAutocompleteViewTest",
    "GeocodeViewTest",
    "AddressActionsViewTest",
    "RevertChangeViewTest",
    "AddTagViewTest",
    "LoadParcelsViewTest",
    "LoadParcelsStatusViewTest",
    ]



class AuthenticatedWebTest(WebTest):
    url_name = None


    def setUp(self):
        self.user = create_user()


    @property
    def url(self):
        return reverse(self.url_name)


    def get(self, ajax=False):
        env = {}
        if ajax:
            env["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        return self.app.get(self.url, user=self.user, extra_environ=env)

    # accept *args so subclasses can use class-level mock-patching
    def test_login_required(self, *args):
        # clear any previous logged-in session
        self.app.reset()

        response = self.app.get(self.url)

        self.assertEqual(response.status_int, 302)



class ImportViewTest(AuthenticatedWebTest):
    url_name = "map_import_addresses"


    def test_get_form_ajax(self):
        res = self.get(ajax=True)

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
        form["tag"] = "mytag"
        form["file"] = ("bad.csv", "Bad, Address, Yo")

        res = form.submit()

        self.assertEqual(
            res.html.findAll("ul", "errorlist")[0].li.text,
            "Value &#39;YO&#39; is not a valid choice.")


    def test_post_form_with_success(self):
        res = self.app.get(
            self.url, user=self.user)

        form = res.forms["import-address-form"]
        form["tag"] = "mytag"
        form["file"] = ("good.csv", "123 Good St, Providence, RI")

        res = form.submit().follow()

        self.assertEqual(
            res.html.findAll("li", "success")[0].p.text,
            "Successfully imported 1 addresses (0 duplicates).")



class MockWriter(object):
    mimetype = "text/mock"
    extension = "mck"

    def __init__(self, addresses):
        self.addresses = addresses


    def save(self, stream):
        # writers might access User FKs and parcel data
        for a in self.addresses:
            a.mapped_by
            a.parcel
        stream.write(",".join([str(a.id) for a in self.addresses]))




@patch("mlt.map.views.EXPORT_FORMATS", ["mock"])
@patch("mlt.map.views.EXPORT_WRITERS", {"mock": MockWriter})
class ExportViewTest(AuthenticatedWebTest):
    url_name = "map_export_addresses"


    def _basic_test(self, querystring):
        res = self.app.get(self.url + querystring, user=self.user)

        self.assertEqual(res.headers["Content-Type"], "text/mock")
        self.assertEqual(
            res.headers["Content-Disposition"],
            "attachment; filename=addresses.mck")

        return res


    def test_export(self, querystring="?export_format=mock"):
        a1 = create_address()
        a2 = create_address()

        res = self._basic_test(querystring)
        self.assertEqual(res.body, "%s,%s" % (a1.id, a2.id))


    def test_queries(self, querystring="?export_format=mock"):
        create_address(mapped_by=create_user())
        create_address()

        # 1 for addresses, 1 for parcels, 11 for misc sessions/auth
        with self.assertNumQueries(13):
            self._basic_test(querystring)


    def test_no_format(self):
        self.test_export("")


    def test_bad_format(self):
        self.test_export("?export_format=blah")


    def test_filter(self):
        a1 = create_address(city="Providence")
        create_address(city="Albuquerque")

        res = self._basic_test("?export_format=mock&city=Providence")

        self.assertEqual(res.body, str(a1.id))



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
        self.assertEqual(a.mapped_by, self.user)
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 1)
        addy = res.json["mapped_to"][0]
        self.assertEqual(addy["id"], a.id)
        self.assertEqual(addy["mapped_timestamp"], date_format(
                utc_to_local(a.mapped_timestamp), "DATETIME_FORMAT"))
        self.assertEqual(addy["needs_review"], True)
        self.assertEqual(addy["has_parcel"], True)
        self.assertEqual(addy["longitude"], res.json["longitude"])


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
        self.assertEqual(a.mapped_by, u)
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 1)
        addy = res.json["mapped_to"][0]
        self.assertEqual(addy["id"], a.id)
        self.assertEqual(addy["needs_review"], False)


    def test_associate_another(self):
        from mlt.dt import utc_to_local

        create_parcel(pl="1234")
        create_address(pl="1234")
        a2 = create_address()

        res = self.post(self.url, {"maptopl": "1234", "aid": a2.id})

        a2 = refresh(a2)
        self.assertEqual(a2.pl, "1234")
        self.assertEqual(a2.mapped_by, self.user)
        self.assertEqual(res.json["pl"], "1234")
        self.assertEqual(len(res.json["mapped_to"]), 2)
        addy = [a for a in res.json["mapped_to"] if a["id"] == a2.id][0]
        self.assertEqual(addy["id"], a2.id)
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
        self.assertEqual(a1.mapped_by, self.user)
        self.assertEqual(a2.mapped_by, self.user)
        self.assertEqual(res.json["pl"], "1234")
        mt = res.json["mapped_to"]
        self.assertEqual(len(mt), 2)
        self.assertEqual(set([a["id"] for a in mt]), set([a1.id, a2.id]))
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
        self.assertEqual(a1.mapped_by, self.user)
        self.assertEqual(a2.mapped_by, self.user)
        self.assertEqual(res.json["pl"], "1234")
        mt = res.json["mapped_to"]
        self.assertEqual(len(mt), 2)
        self.assertEqual(set([a["id"] for a in mt]), set([a1.id, a2.id]))
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

        res = self.get()

        from mlt.map.utils import letter_key

        self.assertEqual(
            [a["index"] for a in res.json["addresses"]],
            [letter_key(i) for i in range(1, 21)])


    def test_queries(self):
        for i in range(50):
            create_address(street_number=str(i+1), pl=i)
            create_parcel(pl=i)

        # 1 for parcels, 1 for addresses, 1 for batches, 11 for sessions/auth
        with self.assertNumQueries(14):
            self.get()



    def test_address_serialization(self):
        self.maxDiff = None

        now = datetime.datetime(2011, 11, 21)
        a = create_address(
            pl="1",
            mapped_by=self.user,
            mapped_timestamp=now)
        b = create_address_batch()
        a.batches.add(b)

        res = self.get()

        from django.utils.formats import date_format
        from mlt.dt import utc_to_local

        self.assertEqual(
            res.json["addresses"],
            [{"add_tag_url": "/map/_add_tag/%s/" % a.id,
              "batch_tags": [
                        {
                            "user": b.user.username,
                            "timestamp": date_format(
                                utc_to_local(b.timestamp), "DATETIME_FORMAT"),
                            "tag": b.tag,
                            }
                        ],
              "city": a.city,
              "complex_name": a.complex_name,
              "edit_url": a.edit_url,
              "id": a.id,
              "index": "A",
              "geocode_failed": False,
              "geocoded": None,
              "has_parcel": False,
              "latitude": None,
              "longitude": None,
              "mapped_by": self.user.username,
              "mapped_timestamp": date_format(
                        utc_to_local(now), "DATETIME_FORMAT"),
              "multi_units": a.multi_units,
              "needs_review": a.needs_review,
              "notes": a.notes,
              "parcel": None,
              "pl": "1",
              "state": a.state,
              "street": a.street,
              "street_name": a.street_name,
              "street_number": a.street_number,
              "street_prefix": a.street_prefix,
              "street_suffix": a.street_suffix,
              "street_type": a.street_type,
              "street_is_parsed": a.street_is_parsed}]
            )


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
            mapped_timestamp=datetime.datetime(2011, 7, 15, 1, 2, 3))
        a2 = create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            mapped_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))
        a3 = create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            mapped_timestamp=datetime.datetime(2011, 7, 16, 1, 2, 3))

        res = self.app.get(
            self.url + "?sort=city&sort=-street&sort=mapped_timestamp",
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


    def test_filter_batch(self):
        a1 = create_address()
        a2 = create_address()
        create_address()

        b1 = create_address_batch(tag="one")
        b2 = create_address_batch(tag="two")

        a1.batches.add(b1, b2)
        a2.batches.add(b2)

        res = self.app.get(
            self.url + "?batches=%s" % b2.id,
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id])


    def test_filter_date_range(self):
        a1 = create_address(
            mapped_timestamp=datetime.datetime(2011, 9, 10))
        create_address(
            mapped_timestamp=datetime.datetime(2011, 10, 10))

        res = self.app.get(
            self.url + "?mapped_timestamp=9/10/2011 to 9/10/2011",
            user=self.user)

        self.assertAddresses(res, [a1.id])


    def test_filter_batch_date_range(self):
        a1 = create_address()
        a2 = create_address()

        b1 = create_address_batch(
            tag="one",
            timestamp=datetime.datetime(2011, 9, 11))
        b2 = create_address_batch(
            tag="two",
            timestamp=datetime.datetime(2011, 9, 12, 1))

        a1.batches.add(b1)
        a2.batches.add(b2)

        res = self.app.get(
            self.url + "?batches__timestamp=9/10/2011 to 9/11/2011",
            user=self.user)

        self.assertAddresses(res, [a1.id])


    def test_filter_multiple_date_ranges_same_field(self):
        a1 = create_address(
            mapped_timestamp=datetime.datetime(2011, 9, 10))
        create_address(
            mapped_timestamp=datetime.datetime(2011, 9, 5))

        res = self.app.get(
            self.url + "?mapped_timestamp=9/10/2011 to 9/11/2011&mapped_timestamp=9/5/2011 to 9/10/2011",
            user=self.user)

        self.assertAddresses(res, [a1.id])


    def test_filter_bad_date_range(self):
        res = self.app.get(
            self.url + "?mapped_timestamp=foobar",
            user=self.user)

        self.assertAddresses(res, [])


    def test_filter_status(self):
        create_address(
            pl="123",
            needs_review=False,
            )
        a2 = create_address(
            pl="234",
            needs_review=True,
            )
        create_address(
            pl="",
            needs_review=False,
            )

        res = self.app.get(
            self.url + "?status=flagged",
            user=self.user)

        self.assertAddresses(res, [a2.id])


    def test_filter_bad_status(self):
        a1 = create_address(
            pl="123",
            needs_review=False,
            )
        a2 = create_address(
            pl="234",
            needs_review=True,
            )
        a3 = create_address(
            pl="",
            needs_review=False,
            )

        res = self.app.get(
            self.url + "?status=foobar",
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id, a3.id])


    def test_filter_plus_ids(self):
        a1 = create_address(
            city="Providence",
            )
        a2 = create_address(
            city="Albuquerque",
            )
        create_address(
            city="Albuquerque",
            )

        res = self.app.get(
            self.url + "?city=Providence&aid=%s" % a2.id,
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id])


    def test_filter_status_plus_ids(self):
        a1 = create_address(
            pl="123",
            needs_review=False,
            )
        a2 = create_address(
            pl="234",
            needs_review=True,
            )
        create_address(
            pl="",
            needs_review=False,
            )

        res = self.app.get(
            self.url + "?status=approved&aid=%s" % a2.id,
            user=self.user)

        self.assertAddresses(res, [a1.id, a2.id])


    def test_filter_case_insensitive(self):
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
            self.url + "?city=providence",
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
            mapped_by=u1,
            )
        a2 = create_address(
            mapped_by=u1,
            )
        create_address(
            mapped_by=u2
            )

        res = self.app.get(
            self.url + "?mapped_by=%s" % u1.id,
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
            )
        create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            )
        create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            )

        res = self.app.get(self.url + "?city=Albuquerque&num=1&count=true", user=self.user)

        self.assertEqual(res.json["count"], 2)
        self.assertEqual(len(res.json["addresses"]), 1)



class HistoryViewTest(AuthenticatedWebTest):
    url_name = "map_history"


    def test_get_changes(self):
        for i in range(50):
            create_address(street_number=str(i+1))

        res = self.get()

        self.assertEqual(
            [c["post"]["street_number"] for c in res.json["changes"]],
            [str(i) for i in range(1, 21)])


    def test_queries(self):
        for i in range(50):
            create_address(street_number=str(i+1), pl=i)
            create_parcel(pl=i)

        # 1 for changes, 1 for parcels, 11 for misc sessions/auth
        with self.assertNumQueries(13):
            self.get()


    def test_change_serialization(self):
        a = create_address()
        c = a.address_changes.get()

        res = self.get()

        from django.utils.formats import date_format
        from mlt.dt import utc_to_local
        self.maxDiff = None
        self.assertEqual(
            res.json["changes"],
            [
                {
                    "id": c.id,
                    "address_id": a.id,
                    "changed_by": c.changed_by.username,
                    "changed_timestamp": date_format(
                        utc_to_local(c.changed_timestamp), "DATETIME_FORMAT"),
                    "pre": None,
                    "revert_url": "/map/_revert/%s/" % c.id,
                    "post": {
                        "city": a.city,
                        "complex_name": a.complex_name,
                        "geocoded": None,
                        "has_parcel": False,
                        "id": c.post.id,
                        "latitude": None,
                        "longitude": None,
                        "mapped_timestamp": None,
                        "multi_units": a.multi_units,
                        "needs_review": a.needs_review,
                        "notes": a.notes,
                        "pl": "",
                        "state": a.state,
                        "street": a.street,
                        "street_name": a.street_name,
                        "street_number": a.street_number,
                        "street_prefix": a.street_prefix,
                        "street_suffix": a.street_suffix,
                        "street_type": a.street_type,
                        "street_is_parsed": a.street_is_parsed
                        },
                    "diff": None,
                    }
                ]
            )


    def test_get_specific_changes(self):
        for i in range(50):
            create_address(street_number=str(i+1))

        res = self.app.get(
            self.url + "?start=%s&num=%s" % (21, 10),
            user=self.user)

        self.assertEqual(
            [a["post"]["street_number"] for a in res.json["changes"]],
            [str(i) for i in range(21, 31)])


    def test_sort(self):
        a1 = create_address(
            input_street="123 N Main St",
            city="Providence",
            )
        c1 = a1.address_changes.get()
        a2 = create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            )
        c2 = a2.address_changes.get()
        a3 = create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            )
        c3 = a3.address_changes.get()

        res = self.app.get(
            self.url + "?sort=post__city&sort=-post__street&sort=changed_timestamp",
            user=self.user)

        self.assertEqual(
            [c["id"] for c in res.json["changes"]],
            [c2.id, c3.id, c1.id]
            )


    def test_sort_bad_field(self):
        res = self.app.get(
            self.url + "?sort=post__city&sort=bad",
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


    def assertChanges(self, response, ids):
        self.assertEqual(
            set([c["id"] for c in response.json["changes"]]),
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
            self.url + "?post__city=Providence",
            user=self.user)

        self.assertChanges(res, [a1.address_changes.get().id])


    def test_filter_batch(self):
        a1 = create_address()
        a2 = create_address()
        create_address()

        b1 = create_address_batch(tag="one")
        b2 = create_address_batch(tag="two")

        a1.batches.add(b1, b2)
        a2.batches.add(b2)

        res = self.app.get(
            self.url + "?address__batches=%s" % b2.id,
            user=self.user)

        self.assertChanges(
            res, [a1.address_changes.get().id, a2.address_changes.get().id])


    def test_filter_same_address(self):
        a1 = create_address(city="Providence")
        a1.city = "Albuquerque"
        a1.save(user=self.user)
        a2 = create_address(city="Albuquerque")
        a2.city = "Providence"
        a2.save(user=self.user)

        res = self.app.get(
            self.url + "?post__city=Providence",
            user=self.user)

        self.assertChanges(
            res,
            [
                a1.address_changes.get(pre__isnull=True).id,
                a2.address_changes.get(pre__isnull=False).id
                ])


    def test_filter_plus_ids(self):
        create_address(
            city="Providence",
            )
        a2 = create_address(
            city="Albuquerque",
            )
        create_address(
            city="Albuquerque",
            )

        res = self.app.get(
            self.url + "?post__city=Albuquerque&address_id=%s" % a2.id,
            user=self.user)

        self.assertChanges(res, [a2.address_changes.get().id])


    def test_filter_status_plus_ids(self):
        create_address(
            pl="123",
            needs_review=False,
            )
        a2 = create_address(
            pl="234",
            needs_review=True,
            )
        create_address(
            pl="",
            needs_review=False,
            )

        res = self.app.get(
            self.url + "?status=approved&address_id=%s" % a2.id,
            user=self.user)

        self.assertChanges(res, [])


    def test_filter_case_insensitive(self):
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
            self.url + "?post__city=providence",
            user=self.user)

        self.assertChanges(res, [a1.address_changes.get().id])


    def test_filter_user(self):
        u1 = create_user()
        u2 = create_user()
        create_address(user=u1)
        create_address(user=u1)
        a3 = create_address(user=u2)

        res = self.app.get(
            self.url + "?changed_by=%s" % u2.id,
            user=self.user)

        self.assertChanges(res, [a3.address_changes.get().id])


    def test_count(self):
        create_address(
            input_street="123 N Main St",
            city="Providence",
            )
        create_address(
            input_street="456 N Main St",
            city="Albuquerque",
            )
        create_address(
            input_street="123 N Main St",
            city="Albuquerque",
            )

        res = self.app.get(
            self.url + "?post__city=Albuquerque&num=1&count=true",
            user=self.user)

        self.assertEqual(res.json["count"], 2)
        self.assertEqual(len(res.json["changes"]), 1)



class AddAddressViewTest(AuthenticatedWebTest):
    url_name = "map_add_address"


    def test_get_form(self):
        response = self.get()

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
                "street_prefix",
                "street_suffix",
                "street_type",
                ]
            )


    def test_post(self):
        response = self.get()
        form = response.form
        form["city"] = "Providence"
        form["state"] = "RI"
        form["street_number"] = "3635"
        form["street_name"] = "Van Gordon",
        form["street_type"] = "St"

        response = form.submit()

        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.json["success"], True)
        from mlt.map.models import Address
        self.assertEqual(Address.objects.count(), 1, response.body)



class AddTagViewTest(CSRFAuthenticatedWebTest):
    def setUp(self):
        super(AddTagViewTest, self).setUp()
        self.address = create_address(city="Providence")


    @property
    def url(self):
        return reverse(
            "map_add_tag", kwargs={"address_id": self.address.id})


    def test_new_batch(self):
        response = self.post(self.url, {"tag": "foo"})

        self.assertEqual(response.status_int, 200)

        self.assertEqual(response.json["address"]["city"], "Providence")
        self.assertEqual(
            response.json["messages"],
            [
                {
                    "level": 25,
                    "message": "New batch 'foo' created.",
                    "tags": "success"
                    }
                ]
            )
        self.assertEqual(response.json["success"], True)

        batch = self.address.batches.get()
        self.assertEqual(batch.tag, "foo")
        self.assertEqual(batch.user, self.user)


    def test_existing_batch(self):
        b = create_address_batch(tag="foo")

        response = self.post(self.url, {"tag": "foo"})

        self.assertEqual(response.status_int, 200)

        self.assertEqual(response.json["address"]["city"], "Providence")
        self.assertEqual(
            response.json["messages"],
            [
                {
                    "level": 25,
                    "message": "Existing batch 'foo' added to address.",
                    "tags": "success"
                    }
                ]
            )
        self.assertEqual(response.json["success"], True)

        batch = self.address.batches.get()
        self.assertEqual(batch, b)


    def test_has_batch(self):
        b = create_address_batch(tag="foo")
        self.address.batches.add(b)

        response = self.post(self.url, {"tag": "foo"})

        self.assertEqual(response.status_int, 200)

        self.assertEqual(
            response.json["messages"],
            [
                {
                    "level": 20,
                    "message": "Address is already in batch 'foo'.",
                    "tags": "info"
                    }
                ]
            )
        self.assertEqual(response.json["success"], False)

        batch = self.address.batches.get()
        self.assertEqual(batch, b)


    def test_no_tag(self):
        response = self.post(self.url, {"tag": ""})

        self.assertEqual(response.status_int, 200)

        self.assertEqual(
            response.json["messages"],
            [
                {
                    "level": 40,
                    "message": "Please provide a batch tag name.",
                    "tags": "error"
                    }
                ]
            )
        self.assertEqual(response.json["success"], False)



class EditAddressViewTest(CSRFAuthenticatedWebTest):
    def setUp(self):
        super(EditAddressViewTest, self).setUp()
        self.address = create_address(city="Albuquerque", geocode_failed=True)


    @property
    def url(self):
        return reverse(
            "map_edit_address", kwargs={"address_id": self.address.id})


    def test_post(self):
        data = {}
        data["city"] = "Providence"
        data["state"] = "RI"
        data["street_number"] = "3635"
        data["street_name"] = "Van Gordon",
        data["street_type"] = "St"

        response = self.post(self.url, data)

        self.assertEqual(response.status_int, 200)

        self.assertEqual(response.json["address"]["city"], "Providence")
        self.assertEqual(
            response.json["address"]["edit_url"],
            "/map/_edit_address/%s/" % self.address.id
            )
        self.assertEqual(len(response.json["messages"]), 1)
        self.assertEqual(response.json["success"], True)

        a = refresh(self.address)

        self.assertEqual(a.city, "Providence")
        # editing an address resets its geocode-failed flag
        self.assertEqual(a.geocode_failed, False)


    def test_errors(self):
        data = {}
        data["city"] = ""
        data["state"] = "XX"
        data["street_number"] = "3635"
        data["street_name"] = "Van Gordon",
        data["street_type"] = "St"

        response = self.post(self.url, data)

        self.assertEqual(response.status_int, 200)

        self.assertEqual(
            response.json,
            {
                "errors": [
                    "The city field is required.",
                    "State: Select a valid choice. "
                    "XX is not one of the available choices."
                    ],
                "messages": [],
                "success": False,
                }
            )

        a = refresh(self.address)

        self.assertEqual(a.city, "Albuquerque")


    def test_non_field_errors(self):
        data = {}
        data["city"] = "Providence"
        data["state"] = "RI"
        data["street_number"] = "3635"
        data["street_name"] = "",
        data["street_type"] = "St"

        response = self.post(self.url, data)

        self.assertEqual(response.status_int, 200)

        self.assertEqual(
            response.json,
            {
                "errors": ['Please enter a street address.'],
                "messages": [],
                "success": False,
                }
            )

        a = refresh(self.address)

        self.assertEqual(a.city, "Albuquerque")



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


    def test_mapped(self):
        p = create_parcel(
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (2.0, 5.0), (1.0, 5.0)]))
        create_address(pl=p.pl)

        response = self.get(
            westlng="0.0", eastlng="3.0", southlat="4.0", northlat="5.5")

        mapped_to = response.json["features"][0]["properties"]["mapped_to"]
        self.assertEqual(len(mapped_to), 1)
        self.assertEqual(mapped_to[0]["street"], "3635 Van Gordon St")


    def test_queries(self):
        p1 = create_parcel(
            pl="1",
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (2.0, 5.0), (1.0, 5.0)]))
        p2 = create_parcel(
            pl="2",
            geom=create_mpolygon(
                [(1.0, 5.0), (1.0, 6.0), (2.0, 6.0), (2.0, 5.0), (1.0, 5.0)]))
        create_address(pl=p1.pl)
        create_address(pl=p2.pl)

        # 1 for parcels, 1 for addresses, 11 for sessions/auth/etc
        with self.assertNumQueries(13):
            self.get(
                westlng="0.0", eastlng="3.0", southlat="4.0", northlat="5.5")



class RevertChangeViewTest(CSRFAuthenticatedWebTest):
    def setUp(self):
        super(RevertChangeViewTest, self).setUp()
        self.address = create_address(city="Providence")


    @property
    def url(self):
        return reverse(
            "map_revert_change",
            kwargs={
                "change_id": self.address.address_changes.get(
                    pre__isnull=True).id
                }
            )


    def test_revert(self):
        res = self.post(self.url, {})
        self.assertEqual(
            res.json,
            {
                "success": True,
                "messages": [
                    {
                        "level": 25,
                        "message": "Change reverted.",
                        "tags": "success"
                        }
                    ]
                }
            )

        a = refresh(self.address)

        self.assertEqual(a.deleted, True)


    def test_revert_noop(self):
        self.post(self.url, {})
        res = self.post(self.url, {})
        self.assertEqual(
            res.json,
            {
                "success": False,
                "messages": [
                    {
                        "level": 30,
                        "message": "This change is already reverted.",
                        "tags": "warning"
                        }
                    ]
                }
            )


    def test_revert_conflict(self):
        self.address.city = "Albuquerque"
        self.address.save(user=self.user)

        self.address.city = "New Bedford"
        self.address.save(user=self.user)

        change = self.address.address_changes.get(post__city="Albuquerque")
        url = reverse("map_revert_change", kwargs={"change_id": change.id})

        res = self.post(url, {})
        self.assertEqual(
            res.json,
            {
                "success": True,
                "messages": [
                    {
                        "level": 25,
                        "message": "Change reverted.",
                        "tags": "success"
                        },
                    {
                        "level": 30,
                        "message":
                            "Reverting this change overwrote more recent "
                        "changes. See "
                        '<a href="#" class="address-history" '
                        'data-address-id="%s">full history</a> '
                        "for this address." % self.address.id,
                        "tags": "warning"
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
            mapped_by=blametern)
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
                    "name": "Albuquerque",
                    "value": "albuquerque",
                    "q": "alb",
                    "rest": "uquerque",
                    }]
            )

        res = self.app.get(self.url + "?q=b", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{      "q": "b",
                    "field": "mapped_by",
                    "name": "blametern",
                    "value": blametern.id,
                    "rest": "lametern",
                    "desc": "mapped by"
                    }]
            )


    def test_batch(self):
        a1 = create_address()
        b2 = create_address_batch(tag="two")

        a1.batches.add(b2)

        res = self.app.get(self.url + "?q=tw", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{
                    "desc": "batch",
                    "field": "batches",
                    "name": "two",
                    "value": b2.id,
                    "q": "tw",
                    "rest": "o",
                    }]
            )


    def test_filter_case(self):
        create_address(
            input_street="123 N Main St",
            city="Providence")
        create_address(
            input_street="456 N Main St",
            city="providence")
        create_address(
            input_street="123 N Main St",
            city="Albuquerque")

        res = self.app.get(self.url + "?q=prov", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{
                    "desc": "city",
                    "field": "city",
                    "name": "providence",
                    "value": "providence",
                    "q": "prov",
                    "rest": "idence",
                    }]
            )


    def test_filter_too_many(self):
        for i in range(100, 120):
            create_address(input_street="%s Main St" % i)

        res = self.app.get(self.url + "?q=1", user=self.user)

        self.assertEqual(res.json["too_many"], ["street"])


    def test_filter_date_suggest(self):
        res = self.app.get(self.url + "?q=8/31+t", user=self.user)

        self.assertEqual(
            res.json["date_suggest"],
            {"q": "8/31 t", "full": "8/31 to [date]", "rest": "o [date]"})


    def test_filter_date_option(self):
        res = self.app.get(self.url + "?q=8-31-11+to+Sep+10+2011", user=self.user)

        self.assertEqual(
            res.json["options"],
            [
                {
                    "desc": "mapped timestamp",
                    "field": "mapped_timestamp",
                    "name": "8/31/2011 to 9/10/2011",
                    "value": "8/31/2011 to 9/10/2011",
                    "q": "8-31-11 to Sep 10 2011",
                    "rest": "",
                    },
                {
                    "desc": "batch timestamp",
                    "field": "batches__timestamp",
                    "name": "8/31/2011 to 9/10/2011",
                    "value": "8/31/2011 to 9/10/2011",
                    "q": "8-31-11 to Sep 10 2011",
                    "rest": "",
                    },
                ]
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



class HistoryAutocompleteViewTest(AuthenticatedWebTest):
    url_name = "map_history_autocomplete"


    def test_filter(self):
        blametern = create_user(username="blametern")
        create_address(
            input_street="123 N Main St",
            city="Providence",
            user=blametern,
            mapped_by=blametern)
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
                    "field": "post__city",
                    "name": "Albuquerque",
                    "value": "albuquerque",
                    "q": "alb",
                    "rest": "uquerque",
                    }]
            )

        res = self.app.get(self.url + "?q=b", user=self.user)

        self.assertEqual(
            res.json["options"],
            [
                {
                    "q": "b",
                    "field": "changed_by",
                    "name": "blametern",
                    "value": blametern.id,
                    "rest": "lametern",
                    "desc": "changed by"
                    },
                {
                    "q": "b",
                    "field": "post__mapped_by",
                    "name": "blametern",
                    "value": blametern.id,
                    "rest": "lametern",
                    "desc": "mapped by"
                    },
             ]
            )


    def test_batch(self):
        a1 = create_address()
        b2 = create_address_batch(tag="two")

        a1.batches.add(b2)

        res = self.app.get(self.url + "?q=tw", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{
                    "desc": "batch",
                    "field": "address__batches",
                    "name": "two",
                    "value": b2.id,
                    "q": "tw",
                    "rest": "o",
                    }]
            )


    def test_filter_case(self):
        create_address(
            input_street="123 N Main St",
            city="Providence")
        create_address(
            input_street="456 N Main St",
            city="providence")
        create_address(
            input_street="123 N Main St",
            city="Albuquerque")

        res = self.app.get(self.url + "?q=prov", user=self.user)

        self.assertEqual(
            res.json["options"],
            [{
                    "desc": "city",
                    "field": "post__city",
                    "name": "providence",
                    "value": "providence",
                    "q": "prov",
                    "rest": "idence",
                    }]
            )


    def test_filter_date_suggest(self):
        res = self.app.get(self.url + "?q=8/31+t", user=self.user)

        self.assertEqual(
            res.json["date_suggest"],
            {"q": "8/31 t", "full": "8/31 to [date]", "rest": "o [date]"})


    def test_filter_date_option(self):
        res = self.app.get(
            self.url + "?q=8-31-11+to+Sep+10+2011", user=self.user)

        self.assertEqual(
            res.json["options"],
            [
                {
                    "desc": "changed timestamp",
                    "field": "changed_timestamp",
                    "name": "8/31/2011 to 9/10/2011",
                    "value": "8/31/2011 to 9/10/2011",
                    "q": "8-31-11 to Sep 10 2011",
                    "rest": "",
                    },
                {
                    "desc": "mapped timestamp",
                    "field": "post__mapped_timestamp",
                    "name": "8/31/2011 to 9/10/2011",
                    "value": "8/31/2011 to 9/10/2011",
                    "q": "8-31-11 to Sep 10 2011",
                    "rest": "",
                    },
                ]
            )


    def test_no_filter(self):
        res = self.get(ajax=True)

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
                    "add_tag_url": "/map/_add_tag/%s/" % a.id,
                    "batch_tags": [],
                    "city": "Providence",
                    "complex_name": "",
                    "edit_url": "/map/_edit_address/%s/" % a.id,
                    "geocode_failed": False,
                    "geocoded": {
                        "latitude": 41.823991,
                        "longitude": -71.406619,
                        },
                    "has_parcel": False,
                    "id": a.id,
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
                    "street_is_parsed": True,
                    "latitude": None,
                    "longitude": None,
                    },
                "success": True,
                }
            )

        geocode.assert_called_with("123 S Main St, Providence, RI")


    def test_geocode_no_id(self):
        res = self.get(ajax=True)

        self.assertEqual(
            res.json["messages"],
            [
                {
                    "message": "Geocoding requires an address 'id' parameter.",
                    "level": 40,
                    "tags": "error"
                    }
                ])

        self.assertFalse(res.json["success"])


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

        self.assertFalse(res.json["success"])


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

        self.assertFalse(res.json["success"])

        geocode.assert_called_with("123 S Main St, Providence, RI")

        a = refresh(a)
        self.assertEqual(a.geocode_failed, True)



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
        create_address(city="Pawtucket")

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


    def test_queries(self):
        a1 = create_address(pl="", needs_review=True)
        a2 = create_address(pl="123", needs_review=True)
        a3 = create_address(pl="234", needs_review=False)

        # 1 to update, 1 for addresses, 1 for parcels, 1 for batches,
        # 1 for querying addresses again to record change, 11 for sessions/auth
        with self.assertNumQueries(16):
            self.post(
                self.url,
                {"aid": [a1.id, a2.id, a3.id], "action": "flag"},
                )


    def test_approve(self):
        a1 = create_address(pl="", needs_review=True)
        a2 = create_address(pl="123", needs_review=True)
        a3 = create_address(pl="234", needs_review=False)

        from django.contrib.auth.models import Permission
        p = Permission.objects.get_by_natural_key(
            "mappings_trusted", "map", "address")
        self.user.user_permissions.add(p)

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
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["addresses"][0]["needs_review"], False)
        self.assertTrue(res.json["success"])
        self.assertEqual(len(res.json["addresses"]), 1)

        a2 = refresh(a2)
        self.assertEqual(a2.needs_review, False)


    def test_approve_no_perm(self):
        a1 = create_address(pl="123", needs_review=True)

        res = self.post(
            self.url,
            {"aid": [a1.id], "action": "approve"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 40,
                    "message":
                        "You don't have permission to approve this mapping.",
                    "tags": "error",
                    }],
            )
        self.assertFalse(res.json["success"])

        a1 = refresh(a1)
        self.assertEqual(a1.needs_review, True)


    def test_approve_by_filter(self):
        a1 = create_address(city="Providence", pl="123", needs_review=True)
        a2 = create_address(city="Pawtucket", pl="123", needs_review=True)
        create_address(city="Providence", pl="123", needs_review=False)
        create_address(city="Providence", pl="")

        from django.contrib.auth.models import Permission
        p = Permission.objects.get_by_natural_key(
            "mappings_trusted", "map", "address")
        self.user.user_permissions.add(p)

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
        # only addresses specifically requested by "aid" are returned
        self.assertEqual(len(res.json["addresses"]), 0)

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
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["addresses"][0]["needs_review"], True)
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
        # only addresses specifically requested by "aid" are returned
        self.assertEqual(len(res.json["addresses"]), 0)

        self.assertEqual(refresh(a1).needs_review, True)
        self.assertEqual(refresh(a2).needs_review, False)


    def test_multi(self):
        a1 = create_address(multi_units=False)
        a2 = create_address(multi_units=True)
        a3 = create_address(multi_units=False)

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id], "action": "multi"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "Address set as multi-unit.",
                    "tags": "success",
                    }],
            )
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["addresses"][0]["id"], a1.id)
        self.assertEqual(res.json["addresses"][0]["multi_units"], True)
        self.assertTrue(res.json["success"])

        a1 = refresh(a1)
        self.assertEqual(a1.multi_units, True)

        a2 = refresh(a2)
        self.assertEqual(a1.multi_units, True)

        a3 = refresh(a3)
        self.assertEqual(a3.multi_units, False)


    def test_single(self):
        a1 = create_address(multi_units=False)
        a2 = create_address(multi_units=True)
        a3 = create_address(multi_units=True)

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id], "action": "single"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "Address set as single unit.",
                    "tags": "success",
                    }],
            )
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["addresses"][0]["id"], a2.id)
        self.assertEqual(res.json["addresses"][0]["multi_units"], False)
        self.assertTrue(res.json["success"])

        a1 = refresh(a1)
        self.assertEqual(a1.multi_units, False)

        a2 = refresh(a2)
        self.assertEqual(a1.multi_units, False)

        a3 = refresh(a3)
        self.assertEqual(a3.multi_units, True)


    def test_reject(self):
        u = create_user()
        now = datetime.datetime.utcnow()
        a1 = create_address(pl="", mapped_by=None, mapped_timestamp=None)
        a2 = create_address(pl="123", mapped_by=u, mapped_timestamp=now)
        a3 = create_address(pl="234", mapped_by=u, mapped_timestamp=now)

        res = self.post(
            self.url,
            {"aid": [a1.id, a2.id], "action": "reject"},
            )

        self.assertEqual(
            res.json["messages"],
            [{
                    "level": 25,
                    "message": "1 mapping rejected.",
                    "tags": "success",
                    }],
            )
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["addresses"][0]["has_parcel"], False)
        self.assertTrue(res.json["success"])

        a2 = refresh(a2)
        self.assertEqual(a2.pl, "")
        self.assertEqual(a2.mapped_by, None)
        self.assertEqual(a2.mapped_timestamp, None)

        a3 = refresh(a3)
        self.assertEqual(a3.pl, "234")
        self.assertEqual(a3.mapped_by, u)
        self.assertEqual(a3.mapped_timestamp, now)


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


class StaffOnlyWebTest(CSRFAuthenticatedWebTest):
    def setUp(self):
        self.user = create_user(is_staff=True)


    def test_staff_required(self, *args):
        # clear any previous logged-in session
        self.app.reset()

        response = self.app.get(self.url, user=create_user(is_staff=False))

        self.assertEqual(response.status_int, 302)


    def test_active_required(self, *args):
        # clear any previous logged-in session
        self.app.reset()

        response = self.app.get(
            self.url, user=create_user(is_staff=True, is_active=False))

        self.assertEqual(response.status_int, 302)



class LoadParcelsViewTest(StaffOnlyWebTest):
    url_name = "map_load_parcels"


    def test_get_form(self):
        res = self.get()

        self.assertIn("multipart/form-data", res.body)
        self.assertEqual(res.templates[0].name, "load_parcels/form.html")


    def test_post_form_with_form_errors(self):
        res = self.get()

        res = res.forms[0].submit()

        self.assertEqual(
            [u.li.text for u in res.html.findAll("ul", "errorlist")],
            ["This field is required."])


    def test_post_form_with_success(self):
        from mlt.map.models import Parcel

        res = self.get()

        p1 = create_parcel(commit=False, pl="1")
        p2 = create_parcel(commit=False, pl="2")

        form = res.forms[0]
        form["shapefile"] = ("parcels.zip", zip_shapefile([p1, p2]).read())

        res = form.submit().follow()

        self.assertEqual(res.status, "200 OK")

        self.assertEqual(Parcel.objects.count(), 2)




class MockResult(object):
    def __init__(self, status="PENDING", info=None):
        self.status = status
        self.info = info


    def ready(self):
        return self.status in ["SUCCESS", "FAILURE"]


    def successful(self):
        return self.status == "SUCCESS"


    def failed(self):
        return self.status == "FAILURE"



@patch("mlt.map.views.tasks.load_parcels_task.AsyncResult")
class LoadParcelsStatusViewTest(StaffOnlyWebTest):
    url_name = "map_load_parcels_status"


    def setUp(self):
        super(LoadParcelsStatusViewTest, self).setUp()


    @property
    def url(self):
        return reverse(self.url_name, kwargs={"task_id": "mock-task-id"})


    def test_get(self, result_class):
        result_class.return_value = MockResult()
        res = self.get()

        self.assertEqual(res.templates[0].name, "load_parcels/status.html")


    def test_ajax_get(self, result_class):
        result_class.return_value = MockResult("PROGRESS", "some info")

        res = self.get(ajax=True)

        self.assertEqual(
            res.json,
            {
                "ready": False,
                "status": "PROGRESS",
                "successful": False,
                "in_progress": True,
                "info": "some info",
                "messages": [],
                }
            )


    def test_ajax_get_pending(self, result_class):
        result_class.return_value = MockResult("PENDING", None)

        res = self.get(ajax=True)

        self.assertEqual(
            res.json,
            {
                "ready": False,
                "status": "PENDING",
                "successful": False,
                "in_progress": False,
                "info": None,
                "messages": [],
                }
            )


    def test_ajax_get_exception(self, result_class):
        result_class.return_value = MockResult("FAILURE", Exception("blah"))

        res = self.get(ajax=True)

        self.assertEqual(
            res.json,
            {
                "ready": True,
                "status": "FAILURE",
                "successful": False,
                "in_progress": False,
                "info": "blah",
                "messages": [],
                }
            )
