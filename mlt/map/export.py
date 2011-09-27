from .writers.csv import CSVWriter
from .writers.xls import XLSWriter



EXPORT_WRITER_LIST = [
    ("CSV", CSVWriter),
    ("XLS", XLSWriter),
    ]


EXPORT_FORMATS = [w[0] for w in EXPORT_WRITER_LIST]


EXPORT_WRITERS = dict(EXPORT_WRITER_LIST)
