from django.http import HttpResponse

from vectorformats.Formats import Django, GeoJSON

from .models import Parcel



def geojson(request):
    qs = Parcel.objects.all().transform().geojson()[:100]
    source = Django.Django(
        geodjango="geom",
        properties=["pl", "address", "first_owner", "classcode"])
    geoj = GeoJSON.GeoJSON()
    output = geoj.encode(source.decode(qs))
    return HttpResponse(output, content_type="application/json")
