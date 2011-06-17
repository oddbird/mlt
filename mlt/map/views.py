from django.http import HttpResponse

from vectorformats.Formats import Django, GeoJSON

from .models import Parcel



def geojson(request, westlat, eastlat, southlng, northlng):
    wkt = (
        "POLYGON(("
        "%(w)s %(s)s, "
        "%(w)s %(n)s, "
        "%(e)s %(n)s, "
        "%(e)s %(s)s, "
        "%(w)s %(s)s"
        "))" % {"w": westlat, "e": eastlat, "s": southlng, "n": northlng}
        )
    qs = Parcel.objects.filter(geom__intersects=wkt)
    source = Django.Django(
        geodjango="geom",
        properties=["pl", "address", "first_owner", "classcode"])
    output = GeoJSON.GeoJSON().encode(source.decode(qs))
    return HttpResponse(output, content_type="application/json")
