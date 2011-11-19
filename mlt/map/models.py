from collections import defaultdict
from datetime import datetime
import re

from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.db.models.query import GeoQuerySet
from django.contrib.localflavor.us.models import USStateField

from .tasks import (
    record_address_change, record_bulk_changes, record_bulk_delete)



class ParcelQuerySet(GeoQuerySet):
    def delete(self):
        super(ParcelQuerySet, self).update(deleted=True)


    def __init__(self, *args, **kwargs):
        super(ParcelQuerySet, self).__init__(*args, **kwargs)

        self._mapped_fetched = False
        self._prefetch_mapped = False


    def prefetch_mapped(self):
        clone = self._clone()

        clone._prefetch_mapped = True

        return clone


    def _clone(self, *args, **kwargs):
        clone = super(ParcelQuerySet, self)._clone(*args, **kwargs)

        clone._prefetch_mapped = self._prefetch_mapped

        return clone


    def __iter__(self):
        if self._prefetch_mapped and not self._mapped_fetched:
            self._fetch_mapped()

        return super(ParcelQuerySet, self).__iter__()


    def _fetch_mapped(self):
        # ensures result cache is fully populated
        len(self)

        addresses_by_pl = defaultdict(list)
        for address in Address.objects.filter(pl__in=[
                p.pl for p in self._result_cache]):
            addresses_by_pl[address.pl].append(address)


        for p in self._result_cache:
            p._mapped_to = addresses_by_pl.get(p.pl, [])
            p._mapped_fetched = True
            for address in p._mapped_to:
                address._parcel = p
                address._parcel_fetched = True

        self._mapped_fetched = True



class ParcelManager(models.GeoManager):
    use_for_related_fields = False


    def get_query_set(self):
        return ParcelQuerySet(self.model, using=self._db).filter(deleted=False)



class Parcel(models.Model):
    pl = models.CharField(max_length=8)
    address = models.CharField(max_length=27)
    first_owner = models.CharField(max_length=254)
    classcode = models.CharField(max_length=55)
    geom = models.MultiPolygonField()

    import_timestamp = models.DateTimeField()
    deleted = models.BooleanField(default=False, db_index=True)

    objects = ParcelManager()


    class Meta:
        unique_together = [("pl", "import_timestamp")]


    def __init__(self, *args, **kwargs):
        super(Parcel, self).__init__(*args, **kwargs)

        self._mapped_to = None
        self._mapped_fetched = False


    def __unicode__(self):
        return self.pl


    def delete(self):
        self.deleted = True
        self.save(force_update=True)


    @property
    def latitude(self):
        return self.geom.centroid.y


    @property
    def longitude(self):
        return self.geom.centroid.x


    @property
    def mapped_to(self):
        """
        List of Addresses mapped to this Parcel.

        """
        if not self._mapped_fetched:
            self._mapped_to = list(Address.objects.filter(pl=self.pl))
            self._mapped_fetched = True

        return self._mapped_to


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


    def __init__(self, *args, **kwargs):
        super(AddressBase, self).__init__(*args, **kwargs)

        self._parcel = None
        self._parcel_fetched = False


    def __unicode__(self):
        return "%s, %s %s" % (
            self.street, self.city, self.state)


    def save(self, *args, **kwargs):
        self.street = (
            self.parsed_street or self.edited_street or self.input_street)
        return super(AddressBase, self).save(*args, **kwargs)


    @property
    def latitude(self):
        if self.parcel:
            return self.parcel.latitude
        return self.geocoded and self.geocoded.y or None


    @property
    def longitude(self):
        if self.parcel:
            return self.parcel.longitude
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
        if not self._parcel_fetched:
            if not self.pl:
                self._parcel = None
            else:
                try:
                    self._parcel = Parcel.objects.get(pl=self.pl)
                except Parcel.DoesNotExist:
                    self._parcel = None
            self._parcel_fetched = True

        return self._parcel


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



class ParcelPrefetchQuerySet(GeoQuerySet):
    def __init__(self, *args, **kwargs):
        super(ParcelPrefetchQuerySet, self).__init__(*args, **kwargs)

        self._parcels_fetched = False
        self._prefetch_parcels = False


    def prefetch_parcels(self):
        clone = self._clone()

        clone._prefetch_parcels = True

        return clone


    def _clone(self, *args, **kwargs):
        clone = super(ParcelPrefetchQuerySet, self)._clone(*args, **kwargs)

        clone._prefetch_parcels = self._prefetch_parcels

        return clone


    def __iter__(self):
        if self._prefetch_parcels and not self._parcels_fetched:
            self._fetch_parcels_wrapper()

        return super(ParcelPrefetchQuerySet, self).__iter__()


    def _fetch_parcels_wrapper(self):
        # ensures result cache is fully populated
        len(self)

        self._fetch_parcels()

        self._parcels_fetched = True


    def _fetch_parcels(self):
        raise NotImplementedError



class AddressQuerySet(ParcelPrefetchQuerySet):
    def prefetch(self):
        return self.select_related(
            "mapped_by", "imported_by").prefetch_parcels()


    def _fetch_parcels(self):
        parcels_by_pl = dict(
            (p.pl, p) for p in
            Parcel.objects.filter(
                pl__in=[a.pl for a in self._result_cache])
            )

        for a in self._result_cache:
            a._parcel = parcels_by_pl.get(a.pl)
            a._parcel_fetched = True
            # can't preset parcel's _mapped_to, address query may not have
            # included all addresses mapped to these parcels


    def update(self, **kwargs):
        user = kwargs.pop("user", None)
        if user is None:
            raise AddressVersioningError(
                "Cannot update addresses without providing user.")

        now = datetime.utcnow()

        # save current values for recording changes
        address_data = {}
        for address in self:
            address_data[address.id] = {"pre": {}, "post": {}}
            for field, value in kwargs.items():
                address_data[address.id]["pre"][field] = getattr(address, field)
                address_data[address.id]["post"][field] = value

        record_bulk_changes.delay(
            address_data=address_data,
            user_id=user.id,
            timestamp=now)

        return super(AddressQuerySet, self).update(**kwargs)


    def delete(self, user=None):
        if user is None:
            raise AddressVersioningError(
                "Cannot delete addresses without providing user.")

        now = datetime.utcnow()

        record_bulk_delete.delay(
            address_ids=[a.id for a in self],
            user_id=user.id,
            timestamp=now)

        super(AddressQuerySet, self).update(deleted=True)



COMPACT_WHITESPACE_RE = re.compile(r"\s+")

def compact_whitespace(s):
    return COMPACT_WHITESPACE_RE.sub(" ", s)


street_replacements = [
    (re.compile(r"\bstreet\b", re.IGNORECASE), "St"),
    (re.compile(r"\bavenue\b", re.IGNORECASE), "Ave"),
    (re.compile(r"\bav\b", re.IGNORECASE), "Ave"),
    ]

def clean_street(s):
    for pattern, repl in street_replacements:
        s = pattern.sub(repl, s)
    return s


class AddressManager(models.GeoManager):
    # even deleted Addresses should be accessible via an AddressChange
    use_for_related_fields = False


    def get_query_set(self):
        return AddressQuerySet(self.model, using=self._db).filter(deleted=False)


    def prefetch(self):
        return self.get_query_set().prefetch()


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
            state = kwargs["state"] = compact_whitespace(state.upper().strip())

        if street is not None:
            street = kwargs["input_street"] = clean_street(
                compact_whitespace(street.strip()).rstrip("."))
            del kwargs["street"]

        if city is not None:
            city = kwargs["city"] = compact_whitespace(city.strip())

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

        pre = self.snapshot_data(saved=True)

        ret = super(Address, self).save(*args, **kwargs)

        post = self.snapshot_data(saved=False)

        record_address_change.delay(
            address_id=self.id,
            user_id=user.id,
            pre_data=pre, post_data=post,
            timestamp=datetime.utcnow())

        return ret


    def delete(self, user=None):
        if user is None:
            raise AddressVersioningError(
                "Cannot delete address without providing user.")

        pre = self.snapshot_data(saved=True)

        self.deleted = True
        super(Address, self).save()

        record_address_change.delay(
            address_id=self.id,
            user_id=user.id,
            pre_data=pre, post_data=None,
            timestamp=datetime.utcnow())


    def undelete(self, user=None):
        if user is None:
            raise AddressVersioningError(
                "Cannot undelete address without providing user.")

        post = self.snapshot_data(saved=True)

        self.deleted = False
        super(Address, self).save()

        record_address_change.delay(
            address_id=self.id,
            user_id=user.id,
            pre_data=None, post_data=post,
            timestamp=datetime.utcnow())


    def snapshot_data(self, saved=True):
        """
        Return a data dictionary representing the state of this Address.

        If ``saved`` is True, this is the state of this address in the
        database. If this is a new, not-yet-saved instance, returns ``None``.

        If ``saved`` is False, this is the current state of this particular
        instance, including any modified fields.

        """
        if saved:
            if self.pk is None:
                return None
            data = self._initial_data.copy()
        else:
            data = self.data(internal=True)

        return data


    @property
    def edit_url(self):
        return reverse("map_edit_address", kwargs={"address_id": self.id})



class AddressSnapshot(AddressBase):
    """
    A snapshot of the state of an Address at a given point in time.

    """
    snapshot_timestamp = models.DateTimeField()



class AddressChangeQuerySet(ParcelPrefetchQuerySet):
    def _fetch_parcels(self):
        pls = set()
        for c in self._result_cache:
            if c.pre is not None:
                pls.add(c.pre.pl)
            if c.post is not None:
                pls.add(c.post.pl)

        parcels_by_pl = dict(
            (p.pl, p) for p in
            Parcel.objects.filter(pl__in=pls))

        for c in self._result_cache:
            if c.pre is not None:
                c.pre._parcel = parcels_by_pl.get(c.pre.pl)
                c.pre._parcel_fetched = True
            if c.post is not None:
                c.post._parcel = parcels_by_pl.get(c.post.pl)
                c.post._parcel_fetched = True



class AddressChangeManager(models.GeoManager):
    def get_query_set(self):
        return AddressChangeQuerySet(self.model, using=self._db)



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


    objects = AddressChangeManager()


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


    def revert(self, user):
        """
        Revert the fields contained in this change's diff to their "pre"
        values.

        Returns a dictionary with possible warning flags about the revert
        action. In the normal case, the returned dictionary will be empty. If
        the reversion overwrites (in part or in full) a more recent change to
        the address, the "conflict" key will be set to a list of the
        conflicting fields. If the reversion is a no-op (nothing needs to be
        changed), the "no-op" key will be set to ``True``.

        """
        changed = False
        conflict = []
        address = self.address

        if self.pre is None:
            if not address.deleted:
                address.delete(user=user)
                changed = True
        elif self.post is None:
            if address.deleted:
                address.undelete(user=user)
                changed = True
        else:
            for field, data in self.diff.items():
                current = getattr(address, field)
                if data["pre"] != current:
                    if data["post"] != current:
                        conflict.append(field)
                    setattr(address, field, data["pre"])
                    changed = True
            if changed:
                address.save(user=user)

        flags = {}

        if not changed:
            flags["no-op"] = True
        if conflict:
            flags["conflict"] = conflict

        return flags


    @property
    def revert_url(self):
        return reverse("map_revert_change", kwargs={"change_id": self.id})
