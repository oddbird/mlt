from datetime import datetime

from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet

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



class AddressBase(models.Model):
    """
    Abstract base class for both Address and AddressState.

    """
    # unmodified input data
    input_street = models.CharField(max_length=200, db_index=True)

    # edited full street, only used if unparsed addresses are edited
    edited_street = models.CharField(max_length=200, blank=True)

    # core address info
    street_prefix = models.CharField(max_length=20, blank=True)
    street_number = models.CharField(max_length=50, blank=True)
    street_name = models.CharField(max_length=100, blank=True)
    street_type = models.CharField(max_length=20, blank=True)
    street_suffix = models.CharField(max_length=20, blank=True)
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
        related_name="%(class)s_mapped")
    mapped_timestamp = models.DateTimeField(blank=True, null=True)
    needs_review = models.BooleanField(default=False, db_index=True)

    # import
    imported_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="%(class)s_imported")
    import_timestamp = models.DateTimeField()
    import_source = models.CharField(max_length=100, db_index=True)


    class Meta:
        abstract = True


    def __unicode__(self):
        return "%s, %s %s" % (
            self.street, self.city, self.state)


    def save(self, *args, **kwargs):
        self.street = (
            self.parsed_street or self.edited_street or self.input_street)
        return super(AddressBase, self).save(*args, **kwargs)


    @property
    def latitude(self):
        parcel = self.parcel
        if parcel:
            return parcel.latitude
        return self.geocoded and self.geocoded.y or None


    @property
    def longitude(self):
        parcel = self.parcel
        if parcel:
            return parcel.longitude
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
    def street_is_parsed(self):
        """
        Returns True if the street address is parsed into its constituent bits,
        False otherwise.

        """
        return bool(self.parsed_street)


    @property
    def parcel(self):
        if not self.pl:
            return None
        try:
            return Parcel.objects.get(pl=self.pl)
        except Parcel.DoesNotExist:
            return None


    @property
    def has_parcel(self):
        return bool(self.parcel)


    def data(self, internal=False):
        """
        Return a dictionary of the full data of this address (all fields which
        should be snapshotted and versioned).

        If ``internal`` is True, uses raw attributes for FKs instead of
        descriptors, making it safe to use in all situations.

        """
        field_attr = "attname" if internal else "name"

        return dict(
            (getattr(field, field_attr),
             getattr(self, getattr(field, field_attr)))
            for field in AddressBase._meta.fields
            )


class AddressQuerySet(QuerySet):
    def update(self, **kwargs):
        user = kwargs.pop("user", None)
        if user is None:
            raise AddressVersioningError(
                "Cannot update addresses without providing user.")

        for address in self:
            pre = address.snapshot(saved=True)
            address.__dict__.update(kwargs)
            post = address.snapshot(saved=False)
            AddressChange.objects.create(
                address=address, changed_by=user, pre=pre, post=post,
                changed_timestamp=datetime.utcnow())

        return super(AddressQuerySet, self).update(**kwargs)


    def delete(self, user=None):
        if user is None:
            raise AddressVersioningError(
                "Cannot delete addresses without providing user.")

        for address in self:
            pre = address.snapshot(saved=True)
            AddressChange.objects.create(
                address=address, changed_by=user, pre=pre, post=None,
                changed_timestamp=datetime.utcnow())

        super(AddressQuerySet, self).update(deleted=True)



class AddressManager(models.GeoManager):
    # even deleted Addresses should be accessible via an AddressChange
    use_for_related_fields = False


    def get_query_set(self):
        return AddressQuerySet(self.model, using=self._db).filter(deleted=False)


    def create_from_input(self, **kwargs):
        """
        Create an address with the given data and return it, unless a duplicate
        existing address is found; then return None.

        If the data is bad (e.g. unknown state) will raise ValidationError.

        """
        user = kwargs.pop("user", None)

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
            obj.save(user=user)
            return obj



class AddressVersioningError(Exception):
    pass



class Address(AddressBase):
    deleted = models.BooleanField(default=False, db_index=True)


    objects = AddressManager()


    class Meta:
        verbose_name_plural = "addresses"
        permissions = [
            (
                "mappings_trusted",
                "Can approve addresses and map with no approval.")
            ]


    def __init__(self, *args, **kwargs):
        super(Address, self).__init__(*args, **kwargs)

        self._initial_data = self.data(internal=True)


    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        if user is None:
            raise AddressVersioningError(
                "Cannot save address without providing user.")

        pre = self.snapshot(saved=True)

        ret = super(Address, self).save(*args, **kwargs)

        post = self.snapshot(saved=False)

        AddressChange.objects.create(
            address=self, changed_by=user, pre=pre, post=post,
            changed_timestamp=datetime.utcnow())

        return ret


    def delete(self, user=None):
        if user is None:
            raise AddressVersioningError(
                "Cannot delete address without providing user.")

        pre = self.snapshot(saved=True)

        self.deleted = True
        super(Address, self).save()

        AddressChange.objects.create(
            address=self, changed_by=user, pre=pre, post=None,
            changed_timestamp=datetime.utcnow())


    def snapshot(self, saved=True):
        """
        Create and return a snapshot of the current state of this Address.

        If ``saved`` is True, this is the state of this address in the
        database. If this is a new, not-yet-saved instance, ``snapshot()`` does
        nothing and returns ``None``.

        If ``saved`` is False, this is the current state of this particular
        instance, including any modified fields.

        """
        if saved:
            if self.pk is None:
                return None
            data = self._initial_data.copy()
        else:
            data = self.data(internal=True)
        data["snapshot_timestamp"] = datetime.utcnow()
        return AddressSnapshot.objects.create(**data)


    @property
    def edit_url(self):
        return reverse("map_edit_address", kwargs={"address_id": self.id})



class AddressSnapshot(AddressBase):
    """
    A snapshot of the state of an Address at a given point in time.

    """
    snapshot_timestamp = models.DateTimeField()



class AddressChange(models.Model):
    """
    Stores information about a change to an Address. The change may encompass
    modifications to multiple fields, but was made by a single user, at a
    single point in time.

    """
    # The Address this change relates to.
    address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="address_changes")

    changed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="address_changes")
    changed_timestamp = models.DateTimeField()

    # The prior snapshot. NULL indicates "address created"
    pre = models.ForeignKey(
        AddressSnapshot, null=True, related_name="pre_for")
    # The post snapshot. NULL indicates "address deleted"
    post = models.ForeignKey(
        AddressSnapshot, null=True, related_name="post_for")


    @property
    def diff(self):
        """
        Return dictionary containing only fields that differ between pre and
        post. If either pre or post is None, return None.

        Each field in the returned dictionary maps to a dictionary with just
        "pre" and "post" keys, containing the "pre" and "post" values of that
        field.

        """
        if self.pre is None or self.post is None:
            return None

        pre_data = self.pre.data()
        post_data = self.post.data()

        diff = {}

        for field in set(pre_data).union(set(post_data)):
            pre = pre_data.get(field)
            post = post_data.get(field)
            if pre != post:
                diff[field] = {"pre": pre, "post": post}

        return diff


    def revert(self):
        """
        Revert the fields contained in this changes' diff to their "pre"
        values.

        Returns a dictionary of fields that have been changed since (i.e. the
        pre-revert value in the address doesn't match this diff's "post"
        value); the user should be warned about these changes.

        Returned dictionary maps field names to dictionary with keys
        "expected", "actual", and "reverted". "expected" and "reverted" are the
        "post" and "pre" values from this diff, respectively, and "actual" is
        the actual value that was found in the pre-revert state of the address.

        """
