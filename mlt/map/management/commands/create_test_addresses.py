import datetime
import random

from django.contrib.auth.models import User
from django.core.management import BaseCommand

from mlt.map.models import Parcel, Address, AddressBatch



class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            num = int(args[0])
        except (IndexError, ValueError):
            num = 100

        users = list(User.objects.all())
        batch = AddressBatch.objects.create(
            user=random.choice(users),
            timestamp=datetime.datetime.utcnow(),
            tag="test-data",
            )

        for p in Parcel.objects.order_by("?")[:num]:
            a = Address(
                input_street=p.address,
                city="Providence",
                state="RI",
                )
            if not random.randint(0, 1):
                a.pl = p.pl
                a.mapped_by = random.choice(users)
                a.mapped_timestamp = datetime.datetime.utcnow()
                if not random.randint(0, 1):
                    a.needs_review = False
            if not random.randint(0, 9):
                a.multi_units = True
            if not random.randint(0, 9):
                a.complex_name = "The Complex"
            if not random.randint(0, 5):
                a.notes = p.classcode

            a.save()
            a.batches.add(batch)
