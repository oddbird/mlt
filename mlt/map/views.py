import json, datetime

from django.core.exceptions import FieldError
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.formats import date_format
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from vectorformats.Formats import Django, GeoJSON

from ..dt import utc_to_local

from .encoder import IterEncoder
from .forms import AddressForm, AddressImportForm
from .importer import ImporterError
from .models import Parcel, Address
from .utils import letter_key
from . import filters, serializers, geocoder



class UIAddressSerializer(serializers.AddressSerializer):
    def _encode_datetime(self, dt):
        if dt:
            return date_format(utc_to_local(dt), "DATETIME_FORMAT")
        return dt



class UIParcelSerializer(serializers.ParcelSerializer):
    default_fields = serializers.ParcelSerializer.default_fields + ["mapped_to"]

    address_serializer = UIAddressSerializer()


    def encode_mapped_to(self, addresses):
        return self.address_serializer.many(addresses)



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
        pl = request.POST["maptopl"]
        parcel = Parcel.objects.get(pl=pl)
    except KeyError:
        messages.error(request, "No PL provided.")
    except Parcel.DoesNotExist:
        messages.error(request, "No parcel with PL '%s'" % pl)

    addresses = filters.apply(Address.objects.all(), request.POST)
    if not addresses:
        messages.error(
            request, "No addresses selected.")

    if parcel and addresses:
        count = addresses.count()
        addresses.update(
            pl=pl,
            mapped_by=request.user,
            mapped_timestamp=datetime.datetime.utcnow(),
            needs_review=not request.user.has_perm(
                "map.mappings_trusted"))
        ret = UIParcelSerializer().one(parcel)
        messages.success(
            request,
            "Mapped %s address%s to PL %s"
            % (
                count,
                "es" if (count != 1) else "",
                pl
                )
            )

    return json_response(ret)



class IndexedAddressSerializer(UIAddressSerializer):
    default_fields = UIAddressSerializer.default_fields + ["index"]


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

    qs = filters.apply(Address.objects.all(), request.GET)

    get_count = request.GET.get("count", "false").lower() not in ["false", "0"]
    if get_count:
        count = qs.count()

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


    qs = sortqs[start-1:start+num-1]

    # @@@ indexing on subsequent queries might break if addresses have been
    # added/deleted?
    ret = []
    for i, address in enumerate(qs):
        address.index = i + start
        ret.append(address)

    data = {
        "addresses": IndexedAddressSerializer(
            extra=["edit_url", "parcel"]).many(ret)
        }

    if get_count:
        data["count"] = count

    return json_response(data)



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
@require_POST
def edit_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id)
    form = AddressForm(request.POST, instance=address)
    if form.is_valid():
        address = form.save(request.user)
        messages.success(
            request, "Address &laquo;%s&raquo; saved." % address.street)
        return json_response({"saved": address.id})
    return json_response({"errors": form.errors})



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
        properties=UIParcelSerializer.default_fields)
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



@login_required
def geocode(request):
    address_id = request.GET.get("id")
    if not address_id:
        messages.error(
            request, "Geocoding requires an address 'id' parameter.")
        return json_response({})

    try:
        address = Address.objects.get(pk=address_id)
    except Address.DoesNotExist:
        messages.error(
            request, "Geocoding: '%s' is not a valid address ID." % address_id)
        return json_response({})

    as_string = geocoder.prep(address)
    data = geocoder.geocode(as_string)

    if not data:
        messages.info(
            request, "Unable to geocode '%s'." % as_string)
        return json_response({})

    geocoder.update(address, data)
    address.save()

    messages.success(
        request, "Address &laquo;%s&raquo; geocoded and updated to &laquo;%s&raquo;" % (as_string, geocoder.prep(address))
        )

    return json_response({
            "address": UIAddressSerializer().one(address),
            })



@login_required
def address_actions(request):
    addresses = filters.apply(Address.objects.all(), request.POST)
    if not addresses:
        messages.error(
            request, "No addresses selected.")
        return json_response({"success": False})

    action = request.POST.get("action")

    if action == "delete":
        count = addresses.count()
        addresses.delete()
        messages.success(
            request, "%s address%s deleted."
            % (count, "es" if (count != 1) else ""))
        return json_response({"success": True})

    if action == "approve":
        addresses = addresses.filter(needs_review=True).exclude(pl="")
        count = addresses.count()
        if not request.user.has_perm("map.mappings_trusted"):
            messages.error(
                request,
                "You don't have permission to approve %s."
                % ("this mapping" if count == 1 else "these mappings"))
            return json_response({"success": False})
        updated = Address.objects.filter(
            id__in=[a.id for a in addresses])
        updated.update(needs_review=False)
        messages.success(
            request, "%s mapping%s approved."
            % (count, "s" if (count != 1) else ""))
        return json_response({
                "success": True,
                "addresses": UIAddressSerializer().many(updated),
                })

    if action == "flag":
        addresses = addresses.filter(needs_review=False).exclude(pl="")
        count = addresses.count()
        updated = Address.objects.filter(
            id__in=[a.id for a in addresses])
        updated.update(needs_review=True)
        messages.success(
            request, "%s mapping%s flagged."
            % (count, "s" if (count != 1) else ""))
        return json_response({
                "success": True,
                "addresses": UIAddressSerializer().many(updated),
                })

    messages.error(request, "Unknown action '%s'" % action)
    return json_response({"success": False})



def json_response(data):
    return HttpResponse(
        json.dumps(data, cls=IterEncoder),
        content_type="application/json")
