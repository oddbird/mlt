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
    seen = set()
    for field, desc in FILTER_FIELDS.items():
        local_field = field.split("__")[0]
        for option in Address.objects.filter(
            **{"%s__istartswith" % field: q}).values_list(
            field, local_field).distinct():
            display, submit = option
            if hasattr(submit, "lower"):
                submit = submit.lower()
            key = (local_field, submit)
            if key not in seen:
                seen.add(key)
                data.append({
                        "q": q,
                        "rest": display[len(q):],
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
            if field == local_part:
                # local char field, need to do case insensitive query
                this_field = Q()
                for val in filter_data.getlist(local_part):
                    this_field = this_field | Q(
                        **{"%s__iexact" % local_part: val})
                filters = filters & this_field
            else:
                # related field, can do straight IN query
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
