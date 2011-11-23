class Serializer(object):
    default_fields = []


    def __init__(self, fields=None, extra=None, exclude=None):
        exclude = set(exclude or [])
        self.fields = [
            f for f in list(fields or self.default_fields) + list(extra or [])
            if f not in exclude
            ]


    def one(self, obj):
        ret = {}
        for field in self.fields:
            val = getattr(obj, field)
            encode_func = getattr(self, "encode_%s" % field, lambda x: x)
            ret[field] = encode_func(val)

        return ret


    def many(self, objs):
        for obj in objs:
            yield self.one(obj)


    def _encode_datetime(self, dt):
        if dt:
            return dt.isoformat()
        return dt


    def _encode_user(self, user):
        if user:
            return user.username
        return user



class ParcelSerializer(Serializer):
    default_fields = [
        "pl",
        "address",
        "first_owner",
        "classcode",
        "latitude",
        "longitude",
        ]



class AddressBatchSerializer(Serializer):
    default_fields = [
        "user",
        "timestamp",
        "tag"
        ]


    def encode_user(self, val):
        return self._encode_user(val)


    def encode_timestamp(self, val):
        return self._encode_datetime(val)



class AddressSerializer(Serializer):
    default_fields = [
        "id",
        "street",
        "street_prefix",
        "street_number",
        "street_name",
        "street_type",
        "street_suffix",
        "street_is_parsed",
        "multi_units",
        "city",
        "state",
        "complex_name",
        "notes",
        "pl",
        "mapped_by",
        "mapped_timestamp",
        "needs_review",
        "geocoded",
        "latitude",
        "longitude",
        ]


    def encode_mapped_timestamp(self, dt):
        return self._encode_datetime(dt)


    def encode_parcel(self, parcel):
        if parcel:
            return ParcelSerializer().one(parcel)
        return parcel


    def encode_mapped_by(self, user):
        return self._encode_user(user)


    def encode_geocoded(self, geocoded):
        if geocoded:
            return {"latitude": geocoded.y, "longitude": geocoded.x}
        return None



class AddressChangeSerializer(Serializer):
    default_fields = [
        "id",
        "address_id",
        "changed_by",
        "changed_timestamp",
        "pre",
        "post",
        "diff",
        ]


    def encode_changed_timestamp(self, dt):
        return self._encode_datetime(dt)


    def encode_changed_by(self, user):
        return self._encode_user(user)


    snapshot_serializer = AddressSerializer()


    def _encode_address_snapshot(self, snapshot):
        if snapshot:
            return self.snapshot_serializer.one(snapshot)


    def encode_pre(self, snapshot):
        return self._encode_address_snapshot(snapshot)


    def encode_post(self, snapshot):
        return self._encode_address_snapshot(snapshot)


    def encode_diff(self, diff):
        # Don't need diff details in a serialization, just need to know the
        # field changed.
        if diff:
            return dict((field, True) for field in diff.keys())
