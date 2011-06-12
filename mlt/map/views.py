from django.http import HttpResponse

from vectorformats.Formats import Django, GeoJSON

from .models import Parcel



def geojson(request, westlat, eastlat, southlon, northlon):
    ewkt = (
        "SRID=4326;POLYGON(("
        "%(w)s %(s)s, "
        "%(w)s %(n)s, "
        "%(e)s %(n)s, "
        "%(e)s %(s)s, "
        "%(w)s %(s)s"
        "))" % {"w": westlat, "e": eastlat, "s": southlon, "n": northlon}
        )
    qs = Parcel.objects.filter(geom__intersects=ewkt).transform()
    source = Django.Django(
        geodjango="geom",
        properties=["pl", "address", "first_owner", "classcode"])
    geoj = GeoJSON.GeoJSON()
    output = geoj.encode(source.decode(qs))
    return HttpResponse(output, content_type="application/json")
