"""
Makes IPython import all of your projects models when shell is started.

1. Save as ipy_user_conf.py in project root
2. ./manage.py shell
3. profit

"""

import IPython.ipapi
ip = IPython.ipapi.get()


def main():
    print "\nImported:\n\n"

    imports = [
        "import datetime",
        "from django.contrib.auth.models import User",
        "from mlt.map.models import Parcel, AddressBatch, AddressBase, Address, AddressChange, AddressSnapshot",
        "from mlt.map.load import load_parcels",
        "from mlt.map import geocoder, serializers",
        ]

    for imp in imports:
        ip.ex(imp)
        print imp

    print "\n"

main()
