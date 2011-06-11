from django.contrib.gis import admin

from .models import Parcel



admin.site.register(Parcel, admin.OSMGeoAdmin)
