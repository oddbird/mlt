from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.account.views",

    url(r"^login/$", "login", name="account_login"),
    url(r"^logout/$", "logout", name="account_logout"),

    url(r"^password_change/$",
        "password_change",
        name="account_password_change"),

    url(r"^password_reset/$",
        "password_reset",
        name="account_password_reset"),

    url(r"^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        "password_reset_confirm",
        name="account_password_reset_confirm"),
)
