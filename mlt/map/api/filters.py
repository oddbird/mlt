from .. import filters



class ApiAddressFilter(filters.AddressFilter):
    fields = filters.AddressFilter.fields + [
        "batches__tag", "mapped_by__username"]



class ApiBatchFilter(filters.Filter):
    fields = [
        "user__username",
        "timestamp",
        "tag"
        ]


    date_fields = set(["timestamp"])
