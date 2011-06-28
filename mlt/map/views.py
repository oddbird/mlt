from django.http import HttpResponse
from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from vectorformats.Formats import Django, GeoJSON

from .forms import AddressForm
from .models import Parcel



@login_required
def add_address(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(request.user)
        return render(
            request, "includes/add_address/success.html", {"address": address})
    return render(request, "includes/add_address/form.html", {"form": form})



@login_required
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
