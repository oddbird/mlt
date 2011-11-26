from django.core.urlresolvers import reverse
from django.utils.functional import wraps

from .. import models, paging, sort
from ..views import json_response
from . import filters, serializers



def api_key_required(viewfunc):
    """
    Decorator for views that require a valid API key in the X-Api-Key header.

    """
    @wraps(viewfunc)
    def _deco(request, *args, **kwargs):
        key = request.META.get("HTTP_X_API_KEY")
        valid_keys = models.ApiKey.objects.filter(key=key)
        if valid_keys.exists():
            return viewfunc(request, *args, **kwargs)
        else:
            return json_response(
                {"success": False, "error": "Invalid API key."},
                status=403)

    return _deco



@api_key_required
def home(request):
    """
    API home; lists available resource URLs.

    """
    return json_response(
        {
            "resource_urls":
                {
                "addresses": reverse("api_addresses"),
                "batches": reverse("api_batches"),
                },
            "success": True,
            })



@api_key_required
def addresses(request):
    """
    API addresses list.

    """
    qs = filters.ApiAddressFilter().apply(
        models.Address.objects.prefetch("batches"),
        request.GET)

    total = qs.count()

    try:
        qs = sort.apply(
            qs, request.GET.getlist("sort") or ["-batches__timestamp"])
    except sort.BadSort as e:
        return json_response(
            {
                "success": False,
                "error": "Bad sort fields: %s" % (", ".join(e.bad_fields)),
                }
            )

    qs = paging.apply(qs, request.GET)

    return json_response(
        {
            "success": True,
            "total": total,
            "addresses": serializers.ApiAddressSerializer(
                exclude=["latitude", "longitude"]).many(qs),
            }
        )



@api_key_required
def batches(request):
    """
    API batches list.

    """
    qs = filters.ApiBatchFilter().apply(
        models.AddressBatch.objects.all(),
        request.GET)

    total = qs.count()

    try:
        qs = sort.apply(
            qs, request.GET.getlist("sort") or ["-timestamp"])
    except sort.BadSort as e:
        return json_response(
            {
                "success": False,
                "error": "Bad sort fields: %s" % (", ".join(e.bad_fields)),
                }
            )

    qs = paging.apply(qs, request.GET)

    return json_response(
        {
            "success": True,
            "total": total,
            "batches": serializers.ApiBatchSerializer().many(qs),
            }
        )
