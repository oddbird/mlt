from django.http import HttpResponse
from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from vectorformats.Formats import Django, GeoJSON

from .forms import AddressForm
from .models import Parcel, Address



@login_required
def addresses(request):
    try:
        start = int(request.GET["start"])
    except (ValueError, KeyError):
        start = 0
    try:
        num = int(request.GET["num"])
    except (ValueError, KeyError):
        num = 20

    # @@@ indexing might break if addresses have been added/deleted?
    addresses = Address.objects.all()[start:start+num]

    return render(request, "includes/addresses.html", {"addresses": addresses})



@login_required
def add_address(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(request.user)
        return render(
            request, "includes/add_address/success.html", {"address": address})
    return render(request, "includes/add_address/form.html", {"form": form})



@login_required
def geojson(request):
    try:
        westlng = request.GET["westlng"]
        eastlng = request.GET["eastlng"]
        northlat = request.GET["northlat"]
        southlat = request.GET["southlat"]
    except KeyError:
        return HttpResponse("{}", content_type="application/json")
    wkt = (
        "POLYGON(("
        "%(w)s %(s)s, "
        "%(w)s %(n)s, "
        "%(e)s %(n)s, "
        "%(e)s %(s)s, "
        "%(w)s %(s)s"
        "))" % {"w": westlng, "e": eastlng, "s": southlat, "n": northlat}
        )
    qs = Parcel.objects.filter(geom__intersects=wkt)
    source = Django.Django(
        geodjango="geom",
        properties=["pl", "address", "first_owner", "classcode"])
    output = GeoJSON.GeoJSON().encode(source.decode(qs))
    return HttpResponse(output, content_type="application/json")
