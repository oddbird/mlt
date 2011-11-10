import csv

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Address



class ImporterError(Exception):
    def __init__(self, errors):
        self.errors = errors



class AddressImporter(object):
    def __init__(self, timestamp, user, source):
        self.extra_data = {
            "import_timestamp": timestamp,
            "imported_by": user,
            "import_source": source,
            "user": user,
            }


    @transaction.commit_manually
    def process(self, rows):
        errors = []
        saved = 0
        dupes = 0
        for i, r in enumerate(rows):
            data = self.extra_data.copy()
            data.update(r)
            try:
                res = Address.objects.create_from_input(**data)
                if res is None:
                    dupes += 1
                else:
                    saved += 1
            except ValidationError as e:
                # 1-based numbering for rows
                errors.append((i + 1, e.message_dict))

        if errors:
            transaction.rollback()
            raise ImporterError(errors)

        transaction.commit()
        return saved, dupes



class CSVAddressImporter(AddressImporter):
    def __init__(self, *args, **kwargs):
        self.fieldnames = kwargs.pop("fieldnames", ["street", "city", "state"])
        self.header = kwargs.pop("header", False)
        super(CSVAddressImporter, self).__init__(*args, **kwargs)


    def process_file(self, fh):
        reader = csv.DictReader(fh, fieldnames=self.fieldnames)
        if self.header:
            reader.next()
        return self.process(reader)
