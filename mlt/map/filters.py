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



LOCAL_FIELDS = [f.split("__")[0] for f in FILTER_FIELDS]



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
                    "rest": display[len(q):],
                    "value": submit,
                    "field": local_field,
                    "desc": desc
                    })

    return data



def apply(qs, filter_data):
    filters = {}
    for field in LOCAL_FIELDS:
        if field in filter_data:
            filters[field] = filter_data[field]

    return qs.filter(**filters)
