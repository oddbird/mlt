from __future__ import absolute_import

import csv

from .base import AddressWriter



class CSVWriter(AddressWriter):
    mimetype = "text/csv"
    extension = "csv"


    def save(self, stream):
        writer = csv.writer(stream)

        writer.writerow(self.field_names)

        for i, row in enumerate(self.serialized(), 1):
            writer.writerow([row[fn] for fn in self.field_names])

        return i
