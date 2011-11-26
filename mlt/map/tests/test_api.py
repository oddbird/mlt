from datetime import datetime

from django.core.urlresolvers import reverse

from django_webtest import WebTest

from .utils import create_address, create_address_batch, create_user
from ..models import ApiKey


__all__ = [
    "ApiHomeViewTest",
    "ApiBatchesViewTest",
    "ApiAddressesViewTest",
    ]



class ApiViewTestCase(WebTest):
    url_name = None

    @property
    def url(self):
        return reverse(self.url_name)


    def setUp(self):
        self.api_key = ApiKey.objects.create(name="testing", key="testing")
        super(ApiViewTestCase, self).setUp()


    def get(self, url=None):
        if url is None:
            url = self.url
        headers = {"X-Api-Key": self.api_key.key}
        return self.app.get(url, headers=headers)


    def test_api_key_required(self):
        res = self.app.get(self.url, expect_errors=True)

        self.assertEqual(res.status_int, 403)
        self.assertEqual(
            res.json,
            {
                "success": False,
                "error": "Invalid API key."
                }
            )



class ApiHomeViewTest(ApiViewTestCase):
    url_name = "api_home"


    def test_home(self):
        res = self.get()

        self.assertEqual(
            res.json,
            {
                "resource_urls":
                    {
                    "addresses": reverse("api_addresses"),
                    "batches": reverse("api_batches"),
                    },
                "success": True,
                }
            )



class ApiListViewTestCase(ApiViewTestCase):
    def test_bad_sort(self):
        res = self.get(self.url + "?sort=foo&sort=bar")

        self.assertEqual(
            res.json,
            {
                "success": False,
                "error": "Bad sort fields: foo, bar",
                }
            )



class ApiBatchesViewTest(ApiListViewTestCase):
    url_name = "api_batches"


    def test_default(self):
        for i in range(25):
            create_address_batch(tag=str(i))

        res = self.get()

        self.assertEqual(res.json["total"], 25)
        self.assertEqual(len(res.json["batches"]), 20)
        self.assertEqual(res.json["success"], True)


    def test_filter_username(self):
        create_address_batch(tag="one")
        create_address_batch(tag="two", user=create_user(username="someone"))

        res = self.get(self.url + "?user__username=someone")

        self.assertEqual(res.json["total"], 1)
        self.assertEqual(len(res.json["batches"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["batches"][0]["tag"], "two")



    def test_filter_tag(self):
        create_address_batch(tag="one")
        create_address_batch(tag="two")

        res = self.get(self.url + "?tag=one")

        self.assertEqual(res.json["total"], 1)
        self.assertEqual(len(res.json["batches"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["batches"][0]["tag"], "one")


    def test_filter_timestamp(self):
        create_address_batch(tag="one", timestamp=datetime(2011, 3, 5, 1))
        create_address_batch(tag="two", timestamp=datetime(2011, 3, 7, 1))

        res = self.get(self.url + "?timestamp=3/4/2011 to 3/6/2011")

        self.assertEqual(res.json["total"], 1)
        self.assertEqual(len(res.json["batches"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["batches"][0]["tag"], "one")


    def test_sort(self):
        create_address_batch(tag="a")
        create_address_batch(tag="b")

        res1 = self.get(self.url + "?sort=tag")
        res2 = self.get(self.url + "?sort=-tag")

        self.assertEqual(
            [b["tag"] for b in res1.json["batches"]], ["a", "b"])
        self.assertEqual(
            [b["tag"] for b in res2.json["batches"]], ["b", "a"])


    def test_paging(self):
        create_address_batch(tag="a")
        create_address_batch(tag="b")

        res = self.get(self.url + "?sort=tag&start=2&num=1")

        self.assertEqual(res.json["total"], 2)
        self.assertEqual(len(res.json["batches"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["batches"][0]["tag"], "b")



class ApiAddressesViewTest(ApiListViewTestCase):
    url_name = "api_addresses"


    def test_default(self):
        for i in range(25):
            create_address()

        res = self.get()

        self.assertEqual(res.json["total"], 25)
        self.assertEqual(len(res.json["addresses"]), 20)
        self.assertEqual(res.json["success"], True)


    def test_filter_mapped_by_username(self):
        create_address(street_name="one")
        create_address(
            street_name="two", mapped_by=create_user(username="someone"))

        res = self.get(self.url + "?mapped_by__username=someone")

        self.assertEqual(res.json["total"], 1)
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["addresses"][0]["street_name"], "two")


    def test_filter_batch_tag(self):
        a1 = create_address(street_name="one")
        a2 = create_address(street_name="two")

        b1 = create_address_batch(tag="one")
        b2 = create_address_batch(tag="two")

        a1.batches.add(b1, b2)
        a2.batches.add(b2)

        res = self.get(self.url + "?batches__tag=one")

        self.assertEqual(res.json["total"], 1)
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["addresses"][0]["street_name"], "one")


    def test_sort(self):
        create_address(street_name="a")
        create_address(street_name="b")

        res1 = self.get(self.url + "?sort=street_name")
        res2 = self.get(self.url + "?sort=-street_name")

        self.assertEqual(
            [b["street_name"] for b in res1.json["addresses"]], ["a", "b"])
        self.assertEqual(
            [b["street_name"] for b in res2.json["addresses"]], ["b", "a"])


    def test_paging(self):
        create_address(street_name="a")
        create_address(street_name="b")

        res = self.get(self.url + "?sort=street_name&start=2&num=1")

        self.assertEqual(res.json["total"], 2)
        self.assertEqual(len(res.json["addresses"]), 1)
        self.assertEqual(res.json["success"], True)

        self.assertEqual(res.json["addresses"][0]["street_name"], "b")
