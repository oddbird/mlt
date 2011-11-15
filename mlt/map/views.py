import json, datetime

from django.core.exceptions import NON_FIELD_ERRORS
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.formats import date_format
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from vectorformats.Formats import GeoJSON
from vectorformats.Feature import Feature

from ..dt import utc_to_local

from .encoder import IterEncoder
from .export import EXPORT_FORMATS, EXPORT_WRITERS
from .filters import AddressFilter, AddressChangeFilter
from .forms import AddressForm, AddressImportForm
from .importer import ImporterError
from .models import Parcel, Address, AddressChange
from .utils import letter_key
from . import serializers, sort, paging, geocoder



class UIDateSerializerMixin(object):
    def _encode_datetime(self, dt):
        if dt:
            return date_format(utc_to_local(dt), "DATETIME_FORMAT")
        return dt



class UIAddressSerializer(UIDateSerializerMixin, serializers.AddressSerializer):
    default_fields = serializers.AddressSerializer.default_fields + [
        "edit_url", "has_parcel"]



class UIParcelSerializer(serializers.ParcelSerializer):
    default_fields = serializers.ParcelSerializer.default_fields + ["mapped_to"]

    address_serializer = UIAddressSerializer()


    def encode_mapped_to(self, addresses):
        return self.address_serializer.many(addresses)



class UISnapshotSerializer(UIDateSerializerMixin,
                           serializers.AddressSerializer):
    default_fields = serializers.AddressSerializer.default_fields + [
        "has_parcel"]



class UIAddressChangeSerializer(UIDateSerializerMixin,
                                serializers.AddressChangeSerializer):
    default_fields = serializers.AddressChangeSerializer.default_fields + [
        "revert_url"]

    snapshot_serializer = UISnapshotSerializer()



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
def export_addresses(request):
    format = request.GET.get("export_format", EXPORT_FORMATS[0])
    writer_class = EXPORT_WRITERS.get(format, EXPORT_WRITERS[EXPORT_FORMATS[0]])

    addresses = AddressFilter().apply(Address.objects.all(), request.GET)

    writer = writer_class(addresses)

    response = HttpResponse(content_type=writer.mimetype)
    response['Content-Disposition'] = (
        'attachment; filename=addresses.%s' % writer.extension)

    writer.save(response)

    return response



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

    addresses = AddressFilter().apply(Address.objects.all(), request.POST)
    if not addresses:
        messages.error(
            request, "No addresses selected.")

    if parcel and addresses:
        count = addresses.count()
        addresses.update(
            user=request.user,
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
    qs = AddressFilter().apply(Address.objects.all(), request.GET)

    get_count = request.GET.get("count", "false").lower() not in ["false", "0"]
    if get_count:
        count = qs.count()

    try:
        qs = sort.apply(qs, request.GET.getlist("sort") or ["import_timestamp"])
    except sort.BadSort as e:
        for field in e.bad_fields:
            messages.error(
                request, "'%s' is not a valid sort field." % field)

    qs = paging.apply(qs, request.GET)

    data = {
        "addresses": IndexedAddressSerializer(
            extra=["parcel"]).many(qs)
        }

    if get_count:
        data["count"] = count

    return json_response(data)



@login_required
def history(request):
    qs = AddressChangeFilter().apply(
        AddressChange.objects.select_related("pre", "post"), request.GET)

    get_count = request.GET.get("count", "false").lower() not in ["false", "0"]
    if get_count:
        count = qs.count()

    try:
        qs = sort.apply(
            qs, request.GET.getlist("sort") or ["changed_timestamp"])
    except sort.BadSort as e:
        for field in e.bad_fields:
            messages.error(
                request, "'%s' is not a valid sort field." % field)

    qs = paging.apply(qs, request.GET)

    data = {
        "changes": UIAddressChangeSerializer().many(qs)
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
        return json_response({"success": True})
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
        return json_response({
                "address": UIAddressSerializer().one(address),
                "success": True,
                })

    # Errors are not displayed by the field, so we need to transform them to
    # always specify which field they relate to.
    errors = []
    for field, field_errors in form.errors.items():
        if field != NON_FIELD_ERRORS:
            modified_errors = []
            for error in field_errors:
                if "This field" in error:
                    error = error.replace("This field", "The %s field" % field)
                else:
                    error = "%s: %s" % (field.title(), error)
                modified_errors.append(error)
            field_errors = modified_errors
        errors.extend(field_errors)
    return json_response({
            "errors": errors,
            "success": False,
            })



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
    features = []
    serializer = UIParcelSerializer()
    for parcel in qs:
        feature = Feature(parcel.id)
        feature.geometry = {
            "type": parcel.geom.geom_type,
            "coordinates": parcel.geom.coords,
            }
        feature.properties = serializer.one(parcel)
        features.append(feature)

    output = GeoJSON.GeoJSON().encode(features, to_string=False)
    return json_response(output)



@login_required
def filter_autocomplete(request):
    q = request.GET.get("q", "")

    if not q:
        messages.error(
            request, "Filter autocomplete requires 'q' parameter.")
        return json_response({})

    data = AddressFilter().autocomplete(Address.objects.all(), q)

    return json_response(data)



@login_required
def history_autocomplete(request):
    q = request.GET.get("q", "")

    if not q:
        messages.error(
            request, "Filter autocomplete requires 'q' parameter.")
        return json_response({})

    data = AddressChangeFilter().autocomplete(AddressChange.objects.all(), q)

    return json_response(data)



@login_required
def geocode(request):
    address_id = request.GET.get("id")
    if not address_id:
        messages.error(
            request, "Geocoding requires an address 'id' parameter.")
        return json_response({"success": False})

    try:
        address = Address.objects.get(pk=address_id)
    except Address.DoesNotExist:
        messages.error(
            request, "Geocoding: '%s' is not a valid address ID." % address_id)
        return json_response({"success": False})

    as_string = geocoder.prep(address)
    data = geocoder.geocode(as_string)

    if not data:
        messages.info(
            request, "Unable to geocode '%s'." % as_string)
        return json_response({"success": False})

    geocoder.update(address, data)
    address.save(user=request.user)

    messages.success(
        request, "Address &laquo;%s&raquo; geocoded and updated to &laquo;%s&raquo;" % (as_string, geocoder.prep(address))
        )

    return json_response({
            "address": UIAddressSerializer().one(address),
            "success": True
            })



@login_required
def address_actions(request):
    addresses = AddressFilter().apply(Address.objects.all(), request.POST)
    if not addresses:
        messages.error(
            request, "No addresses selected.")
        return json_response({"success": False})

    action = request.POST.get("action")

    if action == "delete":
        count = addresses.count()
        addresses.delete(user=request.user)
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
        updated.update(user=request.user, needs_review=False)
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
        updated.update(user=request.user, needs_review=True)
        messages.success(
            request, "%s mapping%s flagged."
            % (count, "s" if (count != 1) else ""))
        return json_response({
                "success": True,
                "addresses": UIAddressSerializer().many(updated),
                })

    if action == "multi":
        addresses = addresses.filter(multi_units=False)
        updated = Address.objects.filter(
            id__in=[a.id for a in addresses])
        updated.update(user=request.user, multi_units=True)
        messages.success(request, "Address set as multi-unit.")
        return json_response({
                "success": True,
                "addresses": UIAddressSerializer().many(updated),
                })

    if action == "single":
        addresses = addresses.filter(multi_units=True)
        updated = Address.objects.filter(
            id__in=[a.id for a in addresses])
        updated.update(user=request.user, multi_units=False)
        messages.success(request, "Address set as single unit.")
        return json_response({
                "success": True,
                "addresses": UIAddressSerializer().many(updated),
                })

    messages.error(request, "Unknown action '%s'" % action)
    return json_response({"success": False})



@login_required
@require_POST
def revert_change(request, change_id):
    change = get_object_or_404(
        AddressChange.objects.select_related("address", "pre", "post"),
        pk=change_id)
    flags = change.revert(request.user)

    success = True

    if flags.get("no-op"):
        success = False
        messages.warning(request, "This change is already reverted.")
    else:
        messages.success(request, "Change reverted.")

    conflict = flags.get("conflict")
    if conflict:
        plural = ""
        conflict_string = conflict[0]
        if len(conflict) > 1:
            plural = "s"
            conflict_string = conflict[:-1].join(", ") + " and " + conflict[-1]
        messages.warning(
            request,
            "Reverting this change overwrote more recent changes to the "
            "%s field%s. See "
            '<a href="#" class="address-history" data-address-id="%s">'
            "full history</a> for this address." % (
                conflict_string, plural, change.address.id
                )
            )

    return json_response({"success": success})



def json_response(data):
    return HttpResponse(
        json.dumps(data, cls=IterEncoder),
        content_type="application/json")
