from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.localflavor.us.models import USStateField

from . import addresses



class Parcel(models.Model):
    pl = models.CharField(max_length=8)
    address = models.CharField(max_length=27)
    first_owner = models.CharField(max_length=254)
    classcode = models.CharField(max_length=55)
    geom = models.MultiPolygonField()

    objects = models.GeoManager()


    def __unicode__(self):
        return self.pl



class StreetSuffix(models.Model):
    suffix = models.CharField(max_length=20, unique=True)


    def __unicode__(self):
        return self.suffix


    class Meta:
        verbose_name_plural = "street suffixes"


    @classmethod
    def suffix_map(cls):
        d = {}
        for s in cls.objects.all().select_related():
            d[s.suffix] = s.suffix
            for a in s.aliases.all():
                d[a.alias] = s.suffix
        return addresses.SuffixMap(d)



class StreetSuffixAlias(models.Model):
    suffix = models.ForeignKey(StreetSuffix, related_name="aliases")
    alias = models.CharField(max_length=20, unique=True)


    def __unicode__(self):
        return self.alias


    class Meta:
        verbose_name_plural = "street suffix aliases"



class Address(models.Model):
    # core address info
    street_number = models.CharField(max_length=50, db_index=True)
    street_name = models.CharField(max_length=100, db_index=True)
    street_suffix = models.CharField(max_length=20, db_index=True)
    multi_units = models.BooleanField(default=False)
    city = models.CharField(max_length=200, db_index=True)
    state = USStateField(db_index=True)
    zip = models.CharField(max_length=5, db_index=True)
    complex_name = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)

    # mapping
    pl = models.CharField(max_length=8, blank=True, db_index=True)

    mapped_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.PROTECT,
        related_name="addresses_mapped")
    mapped_timestamp = models.DateTimeField(blank=True, null=True)
    needs_review = models.BooleanField(default=True, db_index=True)

    # import
    imported_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="addresses_imported")
    import_timestamp = models.DateTimeField()
    import_source = models.CharField(max_length=100, db_index=True)


    def __unicode__(self):
        return "%s %s %s, %s %s %s" % (
            self.street_number, self.street_name, self.street_suffix,
            self.city, self.state, self.zip)


    class Meta:
        verbose_name_plural = "addresses"


    @property
    def street(self):
        return u"%s %s %s" % (
            self.street_number, self.street_name, self.street_suffix)


    StreetNumberError = addresses.StreetNumberError
    StreetSuffixError = addresses.StreetSuffixError


    @staticmethod
    def parse_street(street_address):
        return addresses.parse_street(street_address, StreetSuffix.suffix_map())


    @staticmethod
    def parse_streets(street_addresses):
        suffixmap = StreetSuffix.suffix_map()
        for street_address in street_addresses:
            yield addresses.parse_street(street_address, suffixmap)
