import datetime
from itertools import chain, repeat
import operator

from django.db.models import Q
from django.utils.dateformat import format

from dateutil.parser import parse


MAX_AUTOCOMPLETE = 12


def parse_date(s):
    """
    Add special handling of "yesterday", "today", and "tomorrow" to dateutil's
    parser.

    """
    today = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0)
    one_day = datetime.timedelta(days=1)
    special = {
        "yesterday": today - one_day,
        "today": today,
        "tomorrow": today + one_day,
        }

    s = s.strip()
    if s in special:
        return special[s]

    return parse(s)


def parse_date_range(q):
    """
    Given a string query, attempt to parse it as "[date] to [date]". On failure
    return None, on success return tuple of (fromdate, todate).

    Just "[date]" is also allowed, and parses as the same day for fromdate and
    todate.

    """
    fromto = None

    if not q.strip():
        return None

    bits = (" " + q + " ").split(" to ")
    if len(bits) in (1, 2):
        try:
            fromto = tuple([parse_date(d) for d in bits])
        except ValueError:
            pass
        else:
            if len(fromto) == 1:
                fromto = (fromto[0], fromto[0])

    return fromto



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


    # set of fields to filter raw (no case insensitivity) - usually FKs.
    # should also be listed in "fields".
    raw_fields = set()


    # date/datetime fields to be filtered on a date range. should also be
    # listed in "fields".
    date_fields = set()


    # fields whose values are handled with a custom Q object. maps field names
    # to dictionary mapping value to Q object, or to callable taking list of
    # values and returning Q object. these should not be in "fields".
    special_fields = {}


    # field filters that are ORed after all other filters, rather than ANDed.
    # same format as special_fields. these should not be in "fields".
    override_fields = {}


    def autocomplete(self, qs, q):
        options = []
        too_many = []
        seen = set()
        date_range = parse_date_range(q)
        for field, (display_field, full_field) in self.autocomplete_fields.items():
            if field in self.date_fields:
                if date_range:
                    value = " to ".join([
                            format(dt, "n/j/Y") for dt in date_range])
                    options.append({
                            "q": q,
                            "display_value": value,
                            "value": value,
                            "display_value_rest": "",
                            "field": field,
                            "display_field": display_field,
                            "replace": True,
                            })
            else:
                field_options = (qs.filter(
                        **{"%s__istartswith" % full_field: q}).values_list(
                        full_field, field).distinct())
                if field_options.count() > MAX_AUTOCOMPLETE:
                    too_many.append(display_field)
                    continue
                for option in field_options:
                    display_value, value = option
                    if hasattr(value, "lower"):
                        value = value.lower()
                    key = (field, value)
                    if key not in seen:
                        seen.add(key)
                        options.append({
                                "q": q,
                                "display_value": display_value,
                                "display_value_rest": display_value[len(q):],
                                "value": value,
                                "field": field,
                                "display_field": display_field,
                                "replace": False,
                                })

        return {
            "options": options,
            "too_many": too_many,
            }


    def apply(self, qs, filter_data):
        filters = Q()
        for field in self.fields:
            if field in filter_data:
                if field in self.raw_fields:
                    filters = filters & Q(
                        **{"%s__in" % field: filter_data.getlist(field)})
                elif field in self.date_fields:
                    for q in filter_data.getlist(field):
                        try:
                            from_date, to_date = parse_date_range(q)
                        except (ValueError, TypeError):
                            pass
                        else:
                            filters = filters & Q(
                                **{
                                    "%s__gte" % field: from_date,
                                    "%s__lte" % field:
                                        to_date + datetime.timedelta(days=1),
                                    }
                                  )
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
        "batches",
        "batches__timestamp",
        "street",
        "city",
        "state",
        "pl",
        "mapped_by",
        "mapped_timestamp",
        "complex_name",
        ]


    def get_autocomplete_fields(self):
        ret = super(AddressFilter, self).get_autocomplete_fields()
        ret["mapped_by"] = ("mapped by", "mapped_by__username")
        ret["batches"] = ("batch", "batches__tag")
        ret["batches__timestamp"] = ("batch timestamp", "batches__timestamp")
        return ret


    raw_fields = set(["mapped_by", "batches"])


    date_fields = set(["mapped_timestamp", "batches__timestamp"])


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
        "address__batches",
        "changed_by",
        "changed_timestamp",
        "post__street",
        "post__city",
        "post__state",
        "post__pl",
        "post__mapped_by",
        "post__mapped_timestamp",
        "post__complex_name",
        ]


    def get_autocomplete_fields(self):
        ret = {}
        for field in self.fields:
            ret[field] = (field.replace("post__", "").replace("_", " "), field)
        ret["changed_by"] = ("changed by", "changed_by__username")
        ret["post__mapped_by"] = ("mapped by", "post__mapped_by__username")
        ret["address__batches"] = ("batch", "address__batches__tag")

        return ret


    raw_fields = set(["changed_by", "post__mapped_by", "address__batches"])


    date_fields = set(["changed_timestamp", "post__mapped_timestamp"])


    special_fields = {
        "status": {
            "unmapped": Q(post__pl=""),
            "flagged": ~Q(post__pl="") & Q(post__needs_review=True),
            "approved": ~Q(post__pl="") & Q(post__needs_review=False),
            },
        "address_id": lambda vals: Q(address__in=vals)
        }
