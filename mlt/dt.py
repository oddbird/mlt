from dateutil import tz
from django.conf import settings

utc_tz = tz.gettz("UTC")
server_tz = tz.gettz(settings.TIME_ZONE)

def utc_to_local(dt):
    return dt.replace(tzinfo=utc_tz).astimezone(server_tz)
