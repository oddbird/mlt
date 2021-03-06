import datetime

from django.test import TestCase

from mock import Mock

from .utils import create_address, create_parcel, create_user



__all__ = [
    "SerializerTest",
    "AddressSerializerTest",
    "AddressChangeSerializerTest"
    ]



class SerializerTest(TestCase):
    @property
    def serializer(self):
        from mlt.map.serializers import Serializer

        class SubSerializer(Serializer):
            default_fields = ["field1", "field2"]

        return SubSerializer


    def mock(self, **kwargs):
        defaults = {"field1": "val1", "field2": "val2", "field3": "val3"}
        defaults.update(kwargs)
        ret = Mock()
        ret.__dict__.update(defaults)
        return ret


    def test_one(self):
        self.assertEqual(
            self.serializer().one(self.mock()),
            {"field1": "val1", "field2": "val2"})


    def test_many(self):
        self.assertEqual(
            list(
                self.serializer().many(
                    [self.mock(), self.mock(field2="other2")]
                    )
                ),
            [
                {"field1": "val1", "field2": "val2"},
                {"field1": "val1", "field2": "other2"},
                ]
            )


    def test_fields(self):
        s = self.serializer(fields=["field1"])
        self.assertEqual(s.one(self.mock()), {"field1": "val1"})


    def test_extra(self):
        s = self.serializer(extra=["field3"])
        self.assertEqual(
            s.one(self.mock()),
            {"field1": "val1", "field2": "val2", "field3": "val3"})


    def test_exclude(self):
        s = self.serializer(exclude=["field1"])
        self.assertEqual(s.one(self.mock()), {"field2": "val2"})


    def test_fields_ordered(self):
        s = self.serializer(fields=["one", "two", "three"], extra=["four"])
        self.assertEqual(s.fields, ["one", "two", "three", "four"])


    def test_virtual_fields(self):
        from mlt.map.serializers import Serializer

        class VirtSerializer(Serializer):
            default_fields = ["real_field", "virtual_field"]
            virtual_fields = set(["virtual_field"])


        # if no encode func is defined, virtual field is None
        m = Mock()
        m.real_field = "real"

        self.assertEqual(
            VirtSerializer().one(m),
            {"real_field": "real", "virtual_field": None})

        class BetterVirtSerializer(VirtSerializer):
            def encode_virtual_field(self, obj):
                return "virtual " + obj.real_field

        self.assertEqual(
            BetterVirtSerializer().one(m),
            {"real_field": "real", "virtual_field": "virtual real"})




class AddressSerializerTest(TestCase):
    @property
    def serializer(self):
        from mlt.map.serializers import AddressSerializer
        return AddressSerializer


    def test_datetime(self):
        a = create_address(
            mapped_timestamp=datetime.datetime(2011, 7, 8, 1, 2, 3))

        self.assertEqual(
            self.serializer(["mapped_timestamp"]).one(a),
            {"mapped_timestamp": "2011-07-08T01:02:03"}
            )


    def test_datetime_none(self):
        a = create_address(mapped_timestamp=None)

        self.assertEqual(
            self.serializer(["mapped_timestamp"]).one(a),
            {"mapped_timestamp": None})


    def test_parcel(self):
        create_parcel(pl="1234")
        a = create_address(pl="1234")

        self.assertEqual(
            self.serializer(["parcel"]).one(a)["parcel"]["pl"], "1234")


    def test_parcel_none(self):
        a = create_address(pl="")

        self.assertEqual(
            self.serializer(["parcel"]).one(a), {"parcel": None})


    def test_user(self):
        u = create_user(username="blametern")
        a = create_address(mapped_by=u)

        self.assertEqual(
            self.serializer(["mapped_by"]).one(a),
            {"mapped_by": "blametern"})


    def test_user_none(self):
        a = create_address(mapped_by=None)

        self.assertEqual(
            self.serializer(["mapped_by"]).one(a),
            {"mapped_by": None})





class AddressChangeSerializerTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import AddressChange
        return AddressChange


    @property
    def serializer(self):
        from mlt.map.serializers import AddressChangeSerializer
        return AddressChangeSerializer


    def test_snapshot(self):
        create_address(city="Newark")
        c = self.model.objects.get()

        self.assertEqual(self.serializer().one(c)["post"]["city"], "Newark")


    def test_snapshot_none(self):
        create_address()
        c = self.model.objects.get()

        self.assertEqual(self.serializer().one(c)["pre"], None)


    def test_diff(self):
        a = create_address(mapped_timestamp=datetime.datetime(2011, 11, 11))
        a.mapped_timestamp = datetime.datetime(2011, 11, 12)
        a.save(user=create_user())

        c = self.model.objects.get(pre__isnull=False)

        self.assertEqual(
            self.serializer().one(c)["diff"],
            {"mapped_timestamp": True}
            )
