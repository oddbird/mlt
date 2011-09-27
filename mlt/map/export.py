from .writers.csv import CSVWriter



EXPORT_WRITERS = [
    ("CSV", CSVWriter),
    ]


EXPORT_FORMATS = [w[0] for w in EXPORT_WRITERS]


EXPORT_WRITERS = dict(EXPORT_WRITERS)
