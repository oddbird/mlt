from django.core.urlresolvers import reverse
from django.utils.unittest import TestCase

from django_webtest import WebTest

from .utils import create_address, create_parcel, create_address_batch


__all__ = [
    "AddressAdminTest",
    "ParcelAdminTest",
    "AddressBatchAdminTest",
    "ApiKeyCreationFormTest",
    "ApiKeyAdminTest"
    ]



class AdminTestCase(WebTest):
    model = None


    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            "provplan", "provplan@example.com", "sekritplans")


    def create_instance(self):
        raise NotImplementedError


    @property
    def changelist_url(self):
        return reverse(
            "admin:map_%s_changelist" % self.model._meta.module_name)


    def test_changelist(self):
        instance = self.create_instance()

        response = self.app.get(self.changelist_url, user=self.user)
        response.mustcontain(unicode(instance))


    def test_change(self):
        instance = self.create_instance()

        change_url = reverse(
            "admin:map_%s_change" %
            self.model._meta.module_name, args=[instance.pk])
        response = self.app.get(change_url, user=self.user)
        response.mustcontain(unicode(instance))



class ParcelAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    def create_instance(self):
        return create_parcel()



class AddressAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    def create_instance(self):
        return create_address()


class AddressBatchAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import AddressBatch
        return AddressBatch


    def create_instance(self):
        return create_address_batch()


class ApiKeyCreationFormTest(TestCase):
    @property
    def form(self):
        from mlt.map.admin import ApiKeyCreationForm
        return ApiKeyCreationForm


    def test_save(self):
        f = self.form({"name": "a key"})
        instance = f.save()

        self.assertEqual(instance.name, "a key")


class ApiKeyAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import ApiKey
        return ApiKey


    def create_instance(self):
        return self.model.objects.create(name="testing", key="testing")


    def test_create(self):
        create_url = reverse("admin:map_%s_add" % self.model._meta.module_name)
        response = self.app.get(create_url, user=self.user)

        form = response.forms[0]
        form["name"] = "new key"
        response = form.submit().follow()

        response.mustcontain("new key")
