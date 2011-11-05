from django.core.exceptions import FieldError

from django.contrib import messages



def apply(qs, request):
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

    return sortqs
