from collections import namedtuple
import re



class StreetParsingError(ValueError):
    pass



class StreetNumberError(StreetParsingError):
    pass



class StreetSuffixError(StreetParsingError):
    pass



def parse_street(street_address, suffix_map):
    """
    Parse ``street_address`` (which should be a string like "123 N Main St")
    and returns a namedtuple with ``number``, ``name`` and ``suffix``
    attributes.

    ``suffix_map`` should be a dictionary mapping valid suffix spellings to the
    canonical spelling of that suffix; e.g. it might map both "Street" and "St"
    to "St". (``suffix_map`` can also be a pre-created ``SuffixMap`` instance.)

    If the address cannot be parsed (including if it does not have a valid
    suffix), ``ValueError`` is raised.

    """
    match = STREET_NUMBER_RE.match(street_address)
    if match:
        number = match.group("number")
        sans_number = street_address[match.end():]
    else:
        raise StreetNumberError("No street number found in %r" % street_address)

    name, suffix = SuffixMap(suffix_map).match(sans_number)
    if suffix is None:
        raise StreetSuffixError("No valid suffix found in %r" % street_address)

    return StreetAddress(number=number, name=name, suffix=suffix)



StreetAddress = namedtuple("StreetAddress", ["number", "name", "suffix"])



STREET_NUMBER_RE = re.compile(r"^\s*(?P<number>\d+)\s+")



class SuffixMap(object):
    """
    Instantiate with a dictionary mapping valid suffix spellings to the
    canonical spelling of that suffix; e.g. might map both "St" and "Street" to
    "St".

    Provides a ``match`` method to parse a valid suffix from a street address.

    """
    def __init__(self, suffix_map):
        try:
            # support passing in an existing ``SuffixMap`` instance.
            self._suffixes = suffix_map._suffixes
            self._regex = suffix_map._regex
        except AttributeError:
            self._suffixes = dict(
                (k.lower(), v) for k, v in suffix_map.iteritems())
            self._regex = None


    def match(self, street_address):
        """
        Parses a valid suffix (non-case-sensitive) out of the given
        ``street_address``, returning a tuple (remaining-address,
        canonical-suffix-form).

        If no suffix match is found, returns (passed-in-address, None).

        """
        match = self.regex.search(street_address)
        if match:
            return (
                street_address[:match.start()],
                self._suffixes[match.group("suffix").lower()]
                )
        return (street_address, None)


    @property
    def regex(self):
        if self._regex is None:
            self._regex =  re.compile(
                r"\s+(?P<suffix>%s)\.?\s*$" % "|".join(self._suffixes.keys()),
                flags=re.I)
        return self._regex


    def __getitem__(self, key):
        return self._suffixes[key.lower()]


    def get(self, key, *args, **kwargs):
        return self._suffixes.get(key.lower(), *args, **kwargs)
