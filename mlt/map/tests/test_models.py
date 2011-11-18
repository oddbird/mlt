import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from mock import patch

from .utils import (
    create_parcel, create_address, create_mpolygon, create_user, refresh)



__all__ = ["ParcelTest", "AddressTest", "ParcelPrefetchQuerySetTest"]



class ParcelTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    def test_soft_delete(self):
        p = create_parcel()
        p.delete()
        p = refresh(p)
        self.assertEqual(p.deleted, True)


    def test_soft_bulk_delete(self):
        p = create_parcel()
        self.model.objects.all().delete()
        p = refresh(p)
        self.assertEqual(p.deleted, True)


    def test_latitude(self):
        parcel = create_parcel(
            geom=create_mpolygon([
                    (1.0, 5.0),
                    (1.0, 9.0),
                    (3.0, 9.0),
                    (3.0, 5.0),
                    (1.0, 5.0)]))

        self.assertEqual(parcel.latitude, 7.0)


    def test_longitude(self):
        parcel = create_parcel(
            geom=create_mpolygon([
                    (1.0, 5.0),
                    (1.0, 9.0),
                    (3.0, 9.0),
                    (3.0, 5.0),
                    (1.0, 5.0)]))

        self.assertEqual(parcel.longitude, 2.0)


    def test_mapped_to(self):
        parcel = create_parcel(pl="1234")
        address1 = create_address(pl="1234", needs_review=False)
        create_address(pl="12345")
        address3 = create_address(pl="1234", needs_review=True)
        parcel2 = create_parcel(pl="4321")

        self.assertEqual(
            set(parcel.mapped_to), set([address1, address3]))
        self.assertTrue(parcel.mapped)
        self.assertFalse(parcel2.mapped)


    def test_prefetch_mapped(self):
        create_address(pl="1")
        create_address(pl="2")
        create_address(pl="2")

        create_parcel(pl="1")
        create_parcel(pl="2")

        with self.assertNumQueries(2): # one for parcels, one for addresses
            qs = self.model.objects.all().prefetch_mapped()
            for parcel in qs:
                for address in parcel.mapped_to:
                    self.assertEqual(parcel.pl, address.pl)
                    # both directions are pre-set, no additional query here
                    self.assertEqual(address.parcel, parcel)
            # second iteration shouldn't trigger additional query
            [p for p in qs]



class AddressTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    @property
    def change_model(self):
        from mlt.map.models import AddressChange
        return AddressChange


    @property
    def snapshot_model(self):
        from mlt.map.models import AddressSnapshot
        return AddressSnapshot


    def test_latlong(self):
        a = create_address(geocoded="POINT(30 10)", pl="")

        self.assertEqual(a.latitude, 10)
        self.assertEqual(a.longitude, 30)


    def test_latlong_none(self):
        a = create_address(geocoded=None, pl="")

        self.assertEqual(a.latitude, None)
        self.assertEqual(a.longitude, None)


    def test_latlong_parcel(self):
        a = create_address(geocoded="POINT(30 10)", pl="123")
        create_parcel(
            pl="123",
            geom=create_mpolygon([
                    (1.0, 5.0),
                    (1.0, 9.0),
                    (3.0, 9.0),
                    (3.0, 5.0),
                    (1.0, 5.0)]))


        self.assertEqual(a.latitude, 7.0)
        self.assertEqual(a.longitude, 2.0)


    def test_parsed_street(self):
        a = create_address(
            street_number="123",
            street_name="Main",
            street_type="St")

        self.assertEqual(a.parsed_street, "123 Main St")
        self.assertEqual(a.street_is_parsed, True)


    def test_street_property(self):
        a = create_address(
            street_number="123",
            street_name="Main",
            street_type="St")

        self.assertEqual(a.street, "123 Main St")
        self.assertEqual(a.street_is_parsed, True)


    def test_street_property_unparsed(self):
        a = create_address(
            input_street="123 Main St",
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            )

        self.assertEqual(a.street, "123 Main St")
        self.assertEqual(a.street_is_parsed, False)


    def test_parcel_property(self):
        a = create_address(pl="11 222")
        p = create_parcel(pl="11 222")

        self.assertEqual(a.parcel, p)


    def test_parcel_property_no_such_pl(self):
        a = create_address(pl="11 222")

        self.assertEqual(a.parcel, None)


    def test_parcel_property_no_pl(self):
        a = create_address(pl="")

        self.assertEqual(a.parcel, None)


    def import_data(self):
        try:
            user = self._import_user
        except AttributeError:
            user = self._import_user = create_user()

        return {
            "import_timestamp": datetime.datetime(2011, 7, 8, 1, 2, 3),
            "imported_by": user,
            "import_source": "tests",
            "user": user,
            }


    def create_from_input(self, **kwargs):
        data = self.import_data()
        data.update(kwargs)
        return self.model.objects.create_from_input(**data)


    def test_create(self):
        a = create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="321 S Little St", city="Rapid City", state="SD")

        self.assertNotEqual(a, b)
        self.assertEqual(b.input_street, "321 S Little St")


    def test_create_dupe(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main St", city="Rapid City", state="SD")


        self.assertIs(b, None)
        self.assertEqual(self.model.objects.count(), 1)


    def test_create_dupe_different_case(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 n main st", city="rapid city", state="sd")


        self.assertIs(b, None)


    def test_create_dupe_whitespace(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main  st  ", city=" rapid city", state="  sd")


        self.assertIs(b, None)


    def test_create_dupe_trailing_period(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main St. ", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_dupe_street_st(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main Street", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_dupe_avenue_ave(self):
        create_address(
            input_street="123 N Main Ave", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main Avenue", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_dupe_av_ave(self):
        create_address(
            input_street="123 N Main Ave", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main Av", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_dupe_of_parsed(self):
        create_address(
            input_street="123  N Main St.",
            street_number="123", street_name="N Main", street_type="St",
            city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main St", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_uppercases_state(self):
        a = self.create_from_input(
            street="321 S Little St", city="Rapid City", state="sd")

        self.assertEqual(a.state, "SD")


    def test_create_strips_whitespace(self):
        a = self.create_from_input(
            street="321 S Little St", city=" Rapid City", state=" SD ")

        self.assertEqual(a.state, "SD")


    def test_create_bad_data(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(
                street="123 N Main St", city="Rapid City", state="NOSUCH")


    def test_create_no_state(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(
                street="123 N Main St", city="Rapid City")


    def test_create_no_street(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(city="Rapid City", state="SD")


    def test_data(self):
        data = create_address(city="Providence").data()

        self.assertEqual(data["city"], "Providence")
        self.assertEqual(
            set(data.keys()),
            set([
                    'city',
                    'edited_street',
                    'geocoded',
                    'street',
                    'street_number',
                    'street_name',
                    'mapped_timestamp',
                    'state',
                    'street_suffix',
                    'multi_units',
                    'mapped_by',
                    'input_street',
                    'street_type',
                    'import_timestamp',
                    'needs_review',
                    'imported_by',
                    'import_source',
                    'street_prefix',
                    'complex_name',
                    'notes',
                    'pl'
                    ]))


    def test_data_internal(self):
        data = create_address(city="Providence").data(internal=True)

        # internal uses raw FK id attributes, not descriptors
        self.assertTrue("mapped_by_id" in data)


    def test_snapshot_saved_new(self):
        a = self.model()
        s = a.snapshot(saved=True)

        self.assertIs(s, None)


    def test_snapshot_saved(self):
        a = create_address(city="Providence")
        a.city = "Albuquerque"

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            s = a.snapshot(saved=True)

        self.assertIsInstance(s, self.snapshot_model)
        self.assertEqual(s.city, "Providence")
        self.assertEqual(s.snapshot_timestamp, fake_now)


    def test_snapshot_current(self):
        a = create_address(city="Providence")
        a.city = "Albuquerque"

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            s = a.snapshot(saved=False)

        self.assertIsInstance(s, self.snapshot_model)
        self.assertEqual(s.city, "Albuquerque")
        self.assertEqual(s.snapshot_timestamp, fake_now)


    def test_create_address_change(self):
        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            a = create_address(city="Albuquerque")

        changes = self.change_model.objects.all()

        self.assertEqual(len(changes), 1)

        change = changes[0]

        self.assertEqual(change.address, a)
        self.assertIs(change.pre, None)
        self.assertEqual(change.post.city, "Albuquerque")
        self.assertEqual(change.changed_timestamp, fake_now)


    def test_modify_address_change(self):
        a = create_address(city="Albuquerque")
        user = create_user()

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            a.city = "Providence"
            a.save(user=user)

        changes = self.change_model.objects.all()

        self.assertEqual(len(changes), 2)

        change = changes.get(pre__isnull=False)

        self.assertEqual(change.address, a)
        self.assertEqual(change.pre.city, "Albuquerque")
        self.assertEqual(change.post.city, "Providence")
        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.changed_timestamp, fake_now)


    def test_delete_address_change(self):
        a = create_address(city="Albuquerque")
        user = create_user()

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            a.delete(user=user)

        changes = self.change_model.objects.all()

        self.assertEqual(len(changes), 2)

        change = changes.get(post__isnull=True)

        self.assertEqual(change.address, a)
        self.assertEqual(change.pre.city, "Albuquerque")
        self.assertIs(change.post, None)
        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.changed_timestamp, fake_now)


    def test_bulk_update_address_change(self):
        a = create_address(city="Albuquerque", needs_review=True)
        create_address(city="Providence", needs_review=True)
        qs = self.model.objects.all()
        user = create_user()

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            qs.update(needs_review=False, user=user)

        changes = self.change_model.objects.filter(pre__isnull=False)

        self.assertEqual(len(changes), 2)

        change = changes.get(address=a)

        self.assertEqual(change.pre.needs_review, True)
        self.assertEqual(change.post.needs_review, False)
        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.changed_timestamp, fake_now)


    def test_bulk_delete_address_change(self):
        create_address(city="Albuquerque")
        create_address(city="Providence")
        qs = self.model.objects.all()
        user = create_user()

        fake_now = datetime.datetime(2011, 11, 4, 17, 0, 5)
        with patch("mlt.map.models.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fake_now
            qs.delete(user=user)

        changes = self.change_model.objects.filter(pre__isnull=False)

        self.assertEqual(len(changes), 2)

        change = changes.get(pre__city="Albuquerque")

        self.assertIs(change.post, None)
        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.changed_timestamp, fake_now)


    def test_save_without_user(self):
        from mlt.map.models import AddressVersioningError
        with self.assertRaises(AddressVersioningError):
            self.model.objects.create()


    def test_delete_without_user(self):
        a = create_address()

        from mlt.map.models import AddressVersioningError
        with self.assertRaises(AddressVersioningError):
            a.delete()


    def test_undelete_without_user(self):
        a = create_address()
        a.delete(user=create_user())

        from mlt.map.models import AddressVersioningError
        with self.assertRaises(AddressVersioningError):
            a.undelete()


    def test_bulk_update_without_user(self):
        create_address()
        qs = self.model.objects.all()

        from mlt.map.models import AddressVersioningError
        with self.assertRaises(AddressVersioningError):
            qs.update()


    def test_bulk_delete_without_user(self):
        create_address()
        qs = self.model.objects.all()

        from mlt.map.models import AddressVersioningError
        with self.assertRaises(AddressVersioningError):
            qs.delete()


    def test_create_address_diff(self):
        a = create_address()
        c = a.address_changes.get()

        self.assertEqual(c.diff, None)


    def test_modify_address_diff(self):
        a = create_address(city="Albuquerque", state="NM")
        user = create_user()
        a.city = "Providence"
        a.state = "RI"
        a.save(user=user)

        c = a.address_changes.get(pre__isnull=False)

        self.assertEqual(
            c.diff,
            {
                "city": {"pre": "Albuquerque", "post": "Providence"},
                "state": {"pre": "NM", "post": "RI"},
             }
        )


    def test_delete_address_diff(self):
        a = create_address()
        user = create_user()
        a.delete(user=user)

        c = a.address_changes.get(post__isnull=True)

        self.assertEqual(c.diff, None)


    def test_modify_fk(self):
        u = create_user()
        a = create_address(mapped_by=None)

        a.mapped_by = u
        a.save(user=u)

        change = self.change_model.objects.get(pre__isnull=False)

        self.assertEqual(change.pre.mapped_by, None)
        self.assertEqual(change.post.mapped_by, u)
        self.assertEqual(change.diff, {"mapped_by": {"pre": None, "post": u}})


    def test_revert(self):
        a = create_address(city="Providence")
        a.city = "Albuquerque"
        a.save(user=create_user())

        c = a.address_changes.get(pre__isnull=False)

        u = create_user()
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.city, "Providence")
        self.assertEqual(
            a.address_changes.latest('changed_timestamp').changed_by, u)
        self.assertEqual(flags, {})


    def test_revert_create(self):
        a = create_address()

        c = a.address_changes.get()

        u = create_user()
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.deleted, True)
        change = a.address_changes.latest('changed_timestamp')
        self.assertEqual(change.post, None)
        self.assertEqual(change.changed_by, u)
        self.assertEqual(flags, {})


    def test_revert_delete(self):
        a = create_address()
        a.delete(user=create_user())

        c = a.address_changes.get(post__isnull=True)

        u = create_user()
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.deleted, False)
        change = a.address_changes.latest('changed_timestamp')
        self.assertEqual(change.pre, None)
        self.assertEqual(change.changed_by, u)
        self.assertEqual(flags, {})


    def test_revert_delete_twice(self):
        a = create_address()
        a.delete(user=create_user())

        c = a.address_changes.get(post__isnull=True)

        u = create_user()
        c.revert(u)
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.deleted, False)

        # Second revert had no effect, did not add another change
        # creation, deletion, first revert == 3 changes
        self.assertEqual(len(a.address_changes.all()), 3)
        self.assertEqual(flags, {"no-op": True})



    def test_revert_create_twice(self):
        a = create_address()

        c = a.address_changes.get()

        u = create_user()
        c.revert(u)
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.deleted, True)

        # Second revert had no effect, did not add another change
        # creation, first revert == 2 changes
        self.assertEqual(len(a.address_changes.all()), 2)
        self.assertEqual(flags, {"no-op": True})


    def test_revert_no_change(self):
        a = create_address(city="Providence")
        a.city = "Albuquerque"
        a.save(user=create_user())

        c = a.address_changes.get(pre__isnull=False)

        u = create_user()
        c.revert(u)
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.city, "Providence")

        # Second revert was a no-op, therefore should not add another change
        # creation, edit, first revert == 3 changes
        self.assertEqual(len(a.address_changes.all()), 3)
        self.assertEqual(flags, {"no-op": True})


    def test_revert_conflict(self):
        a = create_address(city="Providence")
        a.city = "Albuquerque"
        a.save(user=create_user())
        a.city = "New Bedford"
        a.save(user=create_user())

        c = a.address_changes.get(post__city="Albuquerque")

        u = create_user()
        flags = c.revert(u)

        a = refresh(a)
        self.assertEqual(a.city, "Providence")
        self.assertEqual(flags, {"conflict": ["city"]})


    def test_prefetch_parcels(self):
        create_address(pl="1")
        create_address(pl="2")

        create_parcel(pl="1")
        create_parcel(pl="2")

        with self.assertNumQueries(2): # one for addresses, one for parcels
            # cloning preserves the prefetch marker
            qs = self.model.objects.all().prefetch_parcels()._clone()
            for address in qs:
                self.assertEqual(address.pl, address.parcel.pl)
            # second iteration shouldn't trigger additional query
            [a.pl for a in qs]


    def test_change_prefetch_parcels(self):
        create_address(pl="1")
        create_address(pl="2")
        a = create_address()
        a.delete(user=create_user())

        create_parcel(pl="1")
        create_parcel(pl="2")

        with self.assertNumQueries(2): # one for changes, one for parcels
            # cloning preserves the prefetch marker
            qs = self.change_model.objects.select_related(
                "pre", "post").prefetch_parcels()._clone()
            for change in qs:
                change.post and change.post.parcel
                change.pre and change.pre.parcel
            # second iteration shouldn't trigger additional query
            [c.post and c.post.parcel for c in qs]



class ParcelPrefetchQuerySetTest(TestCase):
    @property
    def klass(self):
        from mlt.map.models import ParcelPrefetchQuerySet
        return ParcelPrefetchQuerySet


    def test_prefetch_parcel_not_implemented(self):
        qs = self.klass()

        with self.assertRaises(NotImplementedError):
            qs._fetch_parcels()
