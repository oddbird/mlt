from django.conf import settings



def map(request):
    return {
        "TILE_SERVER_URL": settings.TILE_SERVER_URL,
        "MAP_CREDITS": settings.MAP_CREDITS,
        "MAP_DEFAULT_LAT": settings.MAP_DEFAULT_LAT,
        "MAP_DEFAULT_LON": settings.MAP_DEFAULT_LON,
        "MAP_DEFAULT_ZOOM": settings.MAP_DEFAULT_ZOOM,
        }
