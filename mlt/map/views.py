import json, datetime

from django.core.exceptions import FieldError
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from vectorformats.Formats import Django, GeoJSON

from .encoder import IterEncoder
from .forms import AddressForm, AddressImportForm
from .importer import ImporterError
from .models import Parcel, Address
from .utils import letter_key
from . import filters, serializers



@login_required
def import_addresses(request):
    errors = None
    if request.method == "POST":
        form = AddressImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                count, dupes = form.save(request.user)
            except ImporterError as e:
                errors = e.errors
            else:
                messages.success(
                    request,
                    "Successfully imported %s addresses (%s duplicates)."
                    % (count, dupes))
                return redirect("home")
    else:
        form = AddressImportForm()

    template_name = "import/form.html"
    if request.is_ajax():
        template_name = "import/_form.html"

    return render(
        request,
        template_name,
        {"form": form, "errors": errors})



@login_required
def associate(request):
    ret = {}

    parcel = None
    try:
        pl = request.POST["pl"]
        parcel = Parcel.objects.get(pl=pl)
    except KeyError:
        messages.error(request, "No PL provided.")
    except Parcel.DoesNotExist:
        messages.error(request, "No parcel with PL '%s'" % pl)

    aids = request.POST.getlist("aid")
    addresses = Address.objects.filter(id__in=aids)
    if not addresses:
        messages.error(
            request, "No addresses with given IDs (%s)" % ", ".join(aids))

    if parcel and addresses:
        addresses.update(pl=pl, mapped_by=request.user, mapped_timestamp=datetime.datetime.utcnow())
        ret = serializers.ParcelSerializer(extra=["mapped_to"]).one(parcel)
        messages.success(
            request,
            "Mapped %s address%s to PL %s"
            % (
                addresses.count(),
                "es" if (addresses.count() != 1) else "",
                pl
                )
            )

    return json_response(ret)



class IndexedAddressSerializer(serializers.AddressSerializer):
    default_fields = serializers.AddressSerializer.default_fields + ["index"]


    def encode_index(self, val):
        return letter_key(val)



@login_required
def addresses(request):
    try:
        start = int(request.GET["start"])
    except (ValueError, KeyError):
        start = 1
    try:
        num = int(request.GET["num"])
    except (ValueError, KeyError):
        num = 20

    qs = Address.objects.all()

    sort = request.GET.getlist("sort") or ["import_timestamp"]
    sortqs = qs.order_by(*sort)

    try:
        # hack to force evaluation of the sort arguments
        str(sortqs.query)
    except FieldError:
        sortqs = qs
        # apply sorts one at a time to figure out which caused the error
        for sortfield in sort:
            try:
                str(qs.order_by(sortfield).query)
            except FieldError:
                messages.error(
                    request, "'%s' is not a valid sort field." % sortfield)

    qs = filters.apply(sortqs, request.GET)[start-1:start+num-1]

    # @@@ indexing on subsequent queries might break if addresses have been
    # added/deleted?
    ret = []
    for i, address in enumerate(qs):
        address.index = i + start
        ret.append(address)

    return json_response(
        {
            "addresses": IndexedAddressSerializer(
                extra=["parcel"]).many(ret)
            }
        )



@login_required
def add_address(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(request.user)
        messages.success(
            request, "Address &laquo;%s&raquo; added." % address.street)
        return json_response({"added": True})
    return render(request, "includes/add_address/form.html", {"form": form})



@login_required
def geojson(request):
    try:
        westlng = request.GET["westlng"]
        eastlng = request.GET["eastlng"]
        northlat = request.GET["northlat"]
        southlat = request.GET["southlat"]
    except KeyError:
        return json_response({})
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
        properties=serializers.ParcelSerializer.default_fields + ["mapped_to"])
    output = GeoJSON.GeoJSON().encode(source.decode(qs), to_string=False)
    return json_response(output)



@login_required
def filter_autocomplete(request):
    q = request.GET.get("q", "")

    if not q:
        messages.error(
            request, "Filter autocomplete requires 'q' parameter.")
        return json_response({})

    data = filters.autocomplete(q)

    return json_response({"options": data})



def json_response(data):
    return HttpResponse(
        json.dumps(data, cls=IterEncoder),
        content_type="application/json")
