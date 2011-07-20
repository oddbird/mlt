from django.db.models import Q

from .models import Address



FILTER_FIELDS = {
    "street": "street",
    "city": "city",
    "state": "state",
    "pl": "pl",
    "mapped_by__username": "mapped by",
    "imported_by__username": "imported by",
    "import_source": "import source",
    "complex_name": "complex name",
    }



def autocomplete(q):
    data = []
    for field, desc in FILTER_FIELDS.items():
        local_field = field.split("__")[0]
        for option in Address.objects.filter(
            **{"%s__istartswith" % field: q}).values_list(
            field, local_field).distinct():
            display, submit = option
            data.append({
                    "q": q,
                    "display": display,
                    "value": submit,
                    "field": local_field,
                    "desc": desc
                    })

    return data



STATUS_FILTERS = {
    "unmapped": Q(pl=""),
    "flagged": ~Q(pl="") & Q(needs_review=True),
    "approved": ~Q(pl="") & Q(needs_review=False),
    }



def apply(qs, filter_data):
    filters = Q()
    for field in FILTER_FIELDS:
        local_part = field.split("__")[0]
        if local_part in filter_data:
            filters = filters & Q(
                **{"%s__in" % local_part: filter_data.getlist(local_part)})

    if "aid" in filter_data:
        filters = filters & Q(id__in=filter_data.getlist("aid"))

    if "notid" in filter_data:
        filters = filters & ~Q(id__in=filter_data.getlist("notid"))

    status = filter_data.get("status", None)
    if status in STATUS_FILTERS:
        filters = filters & STATUS_FILTERS[status]

    qs = qs.filter(filters)

    return qs
