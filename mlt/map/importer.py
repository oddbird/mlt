from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Address



class AddressImporter(object):
    def __init__(self, timestamp, user, source):
        self.extra_data = {
            "import_timestamp": timestamp,
            "imported_by": user,
            "import_source": source,
            }


    @transaction.commit_manually
    def process(self, rows):
        errors = []
        for i, r in enumerate(rows):
            data = self.extra_data.copy()
            data.update(r)
            try:
                Address.objects.create_from_input(**data)
            except ValidationError as e:
                # 1-based numbering for rows
                errors.append((i + 1, e))

        if errors:
            transaction.rollback()
        else:
            transaction.commit()

        return errors
