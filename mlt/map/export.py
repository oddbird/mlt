from .writers.csv import CSVWriter
from .writers.kml import KMLWriter
from .writers.shp import SHPWriter
from .writers.xls import XLSWriter



EXPORT_WRITER_LIST = [
    ("CSV", CSVWriter),
    ("XLS", XLSWriter),
    ("KML", KMLWriter),
    ("SHP", SHPWriter),
    ]


EXPORT_FORMATS = [w[0] for w in EXPORT_WRITER_LIST]


EXPORT_WRITERS = dict(EXPORT_WRITER_LIST)
