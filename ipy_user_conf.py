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
        "from mlt.map.models import Parcel, Address",
        "from mlt.map.load import load",
        ]

    for imp in imports:
        ip.ex(imp)
        print imp

    print "\n"

main()
