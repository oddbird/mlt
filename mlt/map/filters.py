from itertools import chain, repeat
import operator

from django.db.models import Q



class Filter(object):
    """
    An object that knows how to both provide autocomplete suggestions and
    perform actual filtering for a model.

    """
    # list of filterable fields
    # ("displayname", "data path", "filter path", autocomplete, filter-by-id)
    fields = []


    # mapping of autocompletable fields to tuple:
    # ("field display name", "attribute__path__to__display__value")
    @property
    def autocomplete_fields(self):
        return self.get_autocomplete_fields()


    def get_autocomplete_fields(self):
        ret = {}
        for field in self.fields:
            ret[field] = (field.replace("_", " "), field)
        return ret


    # set of fields to filter raw (no case correction)
    raw_fields = set()


    # fields whose values are handled with a custom Q object. maps field names
    # to dictionary mapping value to Q object, or to callable taking list of
    # values and returning Q object
    special_fields = {}


    # field filters that are ORed after all other filters, rather than ANDed.
    # same format as special_fields
    override_fields = {}


    def autocomplete(self, qs, q):
        data = []
        seen = set()
        for field, (desc, display_field) in self.autocomplete_fields.items():
            for option in qs.filter(
                **{"%s__istartswith" % display_field: q}).values_list(
                display_field, field).distinct():
                display, submit = option
                if hasattr(submit, "lower"):
                    submit = submit.lower()
                key = (field, submit)
                if key not in seen:
                    seen.add(key)
                    data.append({
                            "q": q,
                            "rest": display[len(q):],
                            "value": submit,
                            "field": field,
                            "desc": desc
                            })

        return data


    def apply(self, qs, filter_data):
        filters = Q()
        for field in self.fields:
            if field in filter_data:
                if field in self.raw_fields:
                    filters = filters & Q(
                        **{"%s__in" % field: filter_data.getlist(field)})
                else:
                    q = Q()
                    for val in filter_data.getlist(field):
                        q = q | Q(**{"%s__iexact" % field: val})
                    filters = filters & q

        for op, (field, data) in chain(
            zip(repeat(operator.and_), self.special_fields.items()),
            zip(repeat(operator.or_), self.override_fields.items())
            ):

            if field in filter_data:
                if callable(data):
                    filters = op(filters, data(filter_data.getlist(field)))
                else:
                    value = filter_data.get(field, None)
                    if value in data:
                        filters = op(filters, data[value])

        qs = qs.filter(filters)

        return qs



class AddressFilter(Filter):
    fields = [
        "street",
        "city",
        "state",
        "pl",
        "mapped_by",
        "imported_by",
        "import_source",
        "complex_name",
        ]


    def get_autocomplete_fields(self):
        ret = super(AddressFilter, self).get_autocomplete_fields()
        ret["mapped_by"] = ("mapped by", "mapped_by__username")
        ret["imported_by"] = ("imported by", "imported_by__username")
        return ret


    raw_fields = set(["mapped_by", "imported_by"])


    special_fields = {
        "status": {
            "unmapped": Q(pl=""),
            "flagged": ~Q(pl="") & Q(needs_review=True),
            "approved": ~Q(pl="") & Q(needs_review=False),
            },
        "notid": lambda vals: ~Q(id__in=vals)
        }


    override_fields = {
        "aid": lambda vals: Q(id__in=vals)
        }



class AddressChangeFilter(Filter):
    fields = [
        "changed_by",
        "post__street",
        "post__city",
        "post__state",
        "post__pl",
        "post__mapped_by",
        "post__imported_by",
        "post__import_source",
        "post__complex_name",
        ]


    def get_autocomplete_fields(self):
        ret = super(AddressChangeFilter, self).get_autocomplete_fields()
        ret["changed_by"] = ("changed by", "post__changed_by__username")
        ret["post__mapped_by"] = ("mapped by", "post__mapped_by__username")
        ret["post__imported_by"] = ("imported by", "post__imported_by__username")
        return ret


    raw_fields = set(["changed_by", "post__mapped_by", "post__imported_by"])


    special_fields = {
        "status": {
            "unmapped": Q(post__pl=""),
            "flagged": ~Q(post__pl="") & Q(post__needs_review=True),
            "approved": ~Q(post__pl="") & Q(post__needs_review=False),
            },
        "address_id": lambda vals: Q(address__in=vals)
        }
