from django.core.urlresolvers import reverse
from django_webtest import WebTest

from .utils import create_address, create_suffix, create_alias, create_parcel


__all__ = ["AddressAdminTest", "ParcelAdminTest"]



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



class AddressAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    def create_instance(self):
        return create_address()



class ParcelAdminTest(AdminTestCase):
    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    def create_instance(self):
        return create_parcel()
