from django.core.exceptions import FieldError
from django.db.models import Max



class BadSort(ValueError):
    def __init__(self, bad_fields):
        self.bad_fields = bad_fields
        super(BadSort, self).__init__(
            "Unrecognized fields: %s" % ", ".join(bad_fields))


def apply(qs, sort):
    # Avoid dupe results due to naive order_by across m2m
    if "latest_batch_timestamp" in sort or "-latest_batch_timestamp" in sort:
        qs = qs.annotate(latest_batch_timestamp=Max("batches__timestamp"))
    sortqs = qs.order_by(*sort)

    try:
        # hack to force evaluation of the sort arguments
        str(sortqs.query)
    except FieldError:
        bad_fields = []
        # apply sorts one at a time to figure out which caused the error
        for sortfield in sort:
            try:
                str(qs.order_by(sortfield).query)
            except FieldError:
                bad_fields.append(sortfield)
        raise BadSort(bad_fields)

    return sortqs
