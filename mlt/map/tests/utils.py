from datetime import datetime



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
        }
    defaults.update(kwargs)

    from mlt.map.models import Parcel
    return Parcel.objects.create(**defaults)



def create_suffix(**kwargs):
    defaults = {"suffix": "St"}
    defaults.update(kwargs)

    from mlt.map.models import StreetSuffix
    return StreetSuffix.objects.get_or_create(**defaults)[0]



def create_alias(**kwargs):
    defaults = {
        "alias": "Street",
        "suffix": create_suffix(suffix="St")
        }
    defaults.update(kwargs)

    from mlt.map.models import StreetSuffixAlias
    return StreetSuffixAlias.objects.get_or_create(**defaults)[0]



def create_address(**kwargs):
    defaults = {
        "street_number": "3635",
        "street_name": "Van Gordon",
        "street_suffix": create_suffix(suffix="St"),
        "city": "Providence",
        "state": "RI",
        "zip": "02909",
        "imported_by": create_user(),
        "import_source": "test-created",
        "import_timestamp": datetime(2011, 6, 15, 10, 14, 25),
        }
    defaults.update(kwargs)

    from mlt.map.models import Address
    return Address.objects.create(**defaults)
