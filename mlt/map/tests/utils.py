from datetime import datetime



def refresh(obj):
    return obj.__class__._base_manager.get(pk=obj.pk)



user_number = 1

def create_user(**kwargs):
    global user_number

    password = kwargs.pop("password", None)
    if "username" not in kwargs:
        kwargs["username"] = "test%s" % user_number
        user_number += 1

    from django.contrib.auth.models import User

    user = User(**kwargs)
    if password:
        user.set_password(password)
    user.save()
    return user



def create_mpolygon(points):
    return (
        "MULTIPOLYGON(((%s)))" %
        ", ".join([" ".join([str(lat), str(lng)]) for lat, lng in points]))



def create_parcel(**kwargs):
    commit = kwargs.pop("commit", True)
    defaults = {
        "pl": "111 22",
        "address": "3635 Van Gordon St",
        "first_owner": "Van Gordon",
        "classcode": "Single Family Residence",
        "geom": create_mpolygon([
            ("-71.4057922808270291", "41.7882712655665784"),
            ("-71.4059239736763516", "41.7882228772817541"),
            ("-71.4060543071226732", "41.7884215532894530"),
            ("-71.4059226139629004", "41.7884699426220294"),
            ("-71.4057922808270291", "41.7882712655665784"),
            ]),
        "import_timestamp": datetime.utcnow(),
        }
    defaults.update(kwargs)

    from mlt.map.models import Parcel
    if commit:
        return Parcel.objects.create(**defaults)
    else:
        return Parcel(**defaults)



def create_suffix(suffix="St"):
    from mlt.map.models import StreetSuffix
    return StreetSuffix.objects.get_or_create(suffix=suffix)[0]



def create_alias(alias="Street", suffix=None):
    if suffix is None:
        suffix = create_suffix("St")

    from mlt.map.models import StreetSuffixAlias
    return StreetSuffixAlias.objects.get_or_create(
        alias=alias, suffix=suffix)[0]



def create_address(**kwargs):
    defaults = {
        "input_street": "3635 Van Gordon St",
        "city": "Providence",
        "state": "RI",
        "imported_by": create_user(),
        "import_source": "test-created",
        "import_timestamp": datetime(2011, 6, 15, 10, 14, 25),
        }
    defaults.update(kwargs)

    user = defaults.pop("user", defaults["imported_by"])

    from mlt.map.models import Address
    a = Address(**defaults)
    a.save(user=user)
    return a
