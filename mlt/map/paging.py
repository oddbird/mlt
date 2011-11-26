DEFAULT_PAGE_LENGTH = 20



def apply(qs, GET, index=False):
    start, num = get_start_and_num(GET)
    qs = qs[start-1:start+num-1]

    if index:
        ret = []
        for i, obj in enumerate(qs):
            obj.index = i + start
            ret.append(obj)
    else:
        ret = qs

    return ret




def get_start_and_num(GET):
    start = get_integer(GET, "start", 1)
    num = get_integer(GET, "num", DEFAULT_PAGE_LENGTH)

    return start, num



def get_integer(GET, name, default):
    """
    Pull integer out of querystring, with default.

    """
    try:
        return int(GET[name])
    except (ValueError, KeyError):
        return default
