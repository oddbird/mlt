from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.localflavor.us.models import USStateField



class Parcel(models.Model):
    pl = models.CharField(max_length=8)
    address = models.CharField(max_length=27)
    first_owner = models.CharField(max_length=254)
    classcode = models.CharField(max_length=55)
    geom = models.MultiPolygonField()

    objects = models.GeoManager()


    def __unicode__(self):
        return self.pl


    @property
    def latitude(self):
        return self.geom.centroid.y


    @property
    def longitude(self):
        return self.geom.centroid.x


    @property
    def mapped_addresses(self):
        """
        QuerySet of Addresses mapped to this Parcel.

        """
        return Address.objects.filter(pl=self.pl)


    @property
    def mapped_to(self):
        """
        List of mapped addresses as dictionaries rather than models.

        """
        return [
            {"street": a.street, "needs_review": a.needs_review}
            for a in self.mapped_addresses
            ]


    @property
    def mapped(self):
        """
        Boolean indicator if this parcel is mapped to any addresses.

        """
        return bool(self.mapped_addresses)



class Address(models.Model):
    # unmodified input data
    input_street = models.CharField(max_length=200, db_index=True)

    # core address info
    street_prefix = models.CharField(max_length=20, blank=True, db_index=True)
    street_number = models.CharField(max_length=50, blank=True, db_index=True)
    street_name = models.CharField(max_length=100, blank=True, db_index=True)
    street_type = models.CharField(max_length=20, blank=True, db_index=True)
    street_suffix = models.CharField(max_length=20, blank=True, db_index=True)
    multi_units = models.BooleanField(default=False)
    city = models.CharField(max_length=200, db_index=True)
    state = USStateField(db_index=True)
    complex_name = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)

    # denormalized parsed address for matching with incoming
    parsed_street = models.CharField(
        max_length=200, blank=True, db_index=True)

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
        return "%s, %s %s" % (
            self.street, self.city, self.state)


    def save(self, *args, **kwargs):
        self.parsed_street = self._get_parsed_street()
        return super(Address, self).save(*args, **kwargs)


    class Meta:
        verbose_name_plural = "addresses"


    def _get_parsed_street(self):
        return " ".join([
                elem for elem in [
                    self.street_prefix,
                    self.street_number,
                    self.street_name,
                    self.street_type,
                    self.street_suffix
                    ]
                if elem
                ])


    @property
    def street(self):
        # use _get_parsed_street instead of denormalized parsed_street so it
        # stays up to date even when not saved yet.
        return self._get_parsed_street() or self.input_street


    @property
    def parcel(self):
        try:
            return Parcel.objects.get(pl=self.pl)
        except Parcel.DoesNotExist:
            return None
