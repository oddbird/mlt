import collections
import json



class IterEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, collections.Iterable):
            return list(obj)
        return super(IterEncoder, self).default(obj)
