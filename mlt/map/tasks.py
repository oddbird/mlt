from celery.task import task



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
