from celery.task import task



@task(ignore_result=True)
def record_bulk_delete(address_ids, user_id, timestamp):
    from .models import Address

    for address in Address.objects.filter(id__in=address_ids):
        pre_data = address.snapshot_data(saved=True)
        record_address_change.delay(
            address_id=address.id,
            pre_data=pre_data,
            post_data=None,
            user_id=user_id,
            timestamp=timestamp)



@task(ignore_result=True)
def record_bulk_changes(address_data, user_id, timestamp):
    from .models import Address

    for address in Address.objects.filter(id__in=set(address_data)):
        for k, v in address_data[address.id]["pre"].items():
            setattr(address, k, v)
        pre_data = address.snapshot_data(saved=False)
        for k, v in address_data[address.id]["post"].items():
            setattr(address, k, v)
        post_data = address.snapshot_data(saved=False)
        record_address_change.delay(
            address_id=address.id,
            pre_data=pre_data,
            post_data=post_data,
            user_id=user_id,
            timestamp=timestamp)



@task(ignore_result=True)
def record_address_change(address_id, pre_data, post_data, user_id, timestamp):
    from .models import AddressChange, AddressSnapshot

    if pre_data:
        pre_data["snapshot_timestamp"] = timestamp
        pre = AddressSnapshot.objects.create(**pre_data)
    else:
        pre = None

    if post_data:
        post_data["snapshot_timestamp"] = timestamp
        post = AddressSnapshot.objects.create(**post_data)
    else:
        post = None

    AddressChange.objects.create(
        address_id=address_id,
        changed_by_id=user_id,
        pre=pre,
        post=post,
        changed_timestamp=timestamp)
