from django.utils.formats import date_format



class Serializer(object):
    default_fields = []


    def __init__(self, fields=None, extra=None, exclude=None):
        self.fields = set(
            (fields or self.default_fields) + (extra or [])
            ).difference(set(exclude or []))


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



class ParcelSerializer(Serializer):
    default_fields = [
        "pl",
        "address",
        "first_owner",
        "classcode",
        "mapped",
        ]



class AddressSerializer(Serializer):
    default_fields = [
        "id",
        "street",
        "street_prefix",
        "street_number",
        "street_name",
        "street_type",
        "street_suffix",
        "multi_units",
        "city",
        "state",
        "complex_name",
        "notes",
        "pl",
        "mapped_by",
        "mapped_timestamp",
        "needs_review",
        "imported_by",
        "import_timestamp",
        "import_source"
        ]


    def _encode_datetime(self, dt):
        if dt:
            return date_format(dt, "DATETIME_FORMAT")
        return dt


    encode_mapped_timestamp = _encode_datetime


    encode_import_timestamp = _encode_datetime


    def encode_parcel(self, parcel):
        if parcel:
            return ParcelSerializer().one(parcel)
        return parcel


    def _encode_user(self, user):
        if user:
            return user.username
        return user


    encode_mapped_by = _encode_user


    encode_imported_by = _encode_user

