from django.middleware.csrf import get_token
from django.views.generic.simple import direct_to_template

from django.contrib.auth.decorators import login_required



@login_required
def home(request):
    # force the CSRF middleware's process_response to set the token cookie
    get_token(request)

    return direct_to_template(
        request,
        template="home.html",
        extra_context={
            "user_trusted": request.user.has_perm("map.mappings_trusted")
            }
        )
