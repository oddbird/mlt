from django.core.urlresolvers import reverse

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
    def mapped_to(self):
        """
        QuerySet of Addresses mapped to this Parcel.

        """
        return Address.objects.filter(pl=self.pl)


    @property
    def mapped(self):
        """
        Boolean indicator if this parcel is mapped to any addresses.

        """
        return bool(self.mapped_to)



class AddressManager(models.GeoManager):
    def create_from_input(self, **kwargs):
        """
        Create an address with the given data and return it, unless a duplicate
        existing address is found; then return None.

        If the data is bad (e.g. unknown state) will raise ValidationError.

        """
        street = kwargs.get("street", None)
        city = kwargs.get("city", None)
        state = kwargs.get("state", None)

        if state is not None:
            state = kwargs["state"] = state.upper().strip()

        if street is not None:
            street = kwargs["input_street"] = street.strip()
            del kwargs["street"]

        if city is not None:
            city = kwargs["city"] = city.strip()

        if None not in [street, city, state]:
            dupes = self.filter(
                (
                    models.Q(input_street__iexact=street) |
                    models.Q(street__iexact=street)
                    ) &
                models.Q(city__iexact=city) &
                models.Q(state__iexact=state)
                )
        else:
            dupes = None

        if not dupes:
            obj = self.model(**kwargs)
            obj.full_clean()
            obj.save()
            return obj



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

    # denormalized street address for sorting and matching with incoming
    street = models.CharField(
        max_length=200, blank=True, db_index=True)

    # lat/lon data from geocoding
    geocoded = models.PointField(blank=True, null=True)

    # mapping
    pl = models.CharField(max_length=8, blank=True, db_index=True)

    mapped_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.PROTECT,
        related_name="addresses_mapped")
    mapped_timestamp = models.DateTimeField(blank=True, null=True)
    needs_review = models.BooleanField(default=False, db_index=True)

    # import
    imported_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="addresses_imported")
    import_timestamp = models.DateTimeField()
    import_source = models.CharField(max_length=100, db_index=True)

    objects = AddressManager()


    def __unicode__(self):
        return "%s, %s %s" % (
            self.street, self.city, self.state)


    def save(self, *args, **kwargs):
        self.street = self.parsed_street or self.input_street
        return super(Address, self).save(*args, **kwargs)


    class Meta:
        verbose_name_plural = "addresses"
        permissions = [
            (
                "mappings_trusted",
                "Can approve addresses and map with no approval.")
            ]


    @property
    def latitude(self):
        return self.geocoded and self.geocoded.y or None


    @property
    def longitude(self):
        return self.geocoded and self.geocoded.x or None


    @property
    def parsed_street(self):
        return " ".join([
                elem for elem in [
                    self.street_number,
                    self.street_prefix,
                    self.street_name,
                    self.street_type,
                    self.street_suffix
                    ]
                if elem
                ])


    @property
    def parcel(self):
        try:
            return Parcel.objects.get(pl=self.pl)
        except Parcel.DoesNotExist:
            return None


    @property
    def edit_url(self):
        return reverse("map_edit_address", kwargs={"address_id": self.id})
