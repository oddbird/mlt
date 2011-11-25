import csv

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Address, AddressBatch



class ImporterError(Exception):
    def __init__(self, errors):
        self.errors = errors



class AddressImporter(object):
    def __init__(self, timestamp, user, tag):
        self.batch = AddressBatch.objects.create(
            timestamp=timestamp, user=user, tag=tag)
        self.extra_data = {"user": user}


    @transaction.commit_manually
    def process(self, rows):
        errors = []
        saved = 0
        dupes = 0
        for i, r in enumerate(rows, 1):
            data = self.extra_data.copy()
            data.update(r)
            try:
                created, addresses = Address.objects.create_from_input(**data)
                if created:
                    saved += 1
                else:
                    dupes += 1
            except ValidationError as e:
                errors.append((i, e.message_dict))
            except TypeError:
                transaction.rollback()
                raise ImporterError(
                    [(i, {"?": [u"Extra or unknown columns in input."]})])
            except:
                transaction.rollback()
                raise
            else:
                self.batch.addresses.add(*addresses)

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
        def filtered_reader():
            for record in csv.DictReader(fh, fieldnames=self.fieldnames):
                if None in record:
                    del record[None]
                yield record

        reader = filtered_reader()

        if self.header:
            reader.next()
        return self.process(reader)
