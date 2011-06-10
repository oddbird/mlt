from django.contrib.auth import forms as auth_forms

import floppyforms as forms

from ..core.forms import FloppyWidgetsMixin, NonFieldErrorsMixin



class AuthenticationForm(FloppyWidgetsMixin,
                         NonFieldErrorsMixin,
                         auth_forms.AuthenticationForm):
    pass



class PasswordResetForm(FloppyWidgetsMixin,
                        NonFieldErrorsMixin,
                        auth_forms.PasswordResetForm):
    widget_classes = {"email": forms.EmailInput}



class SetPasswordForm(FloppyWidgetsMixin,
                      NonFieldErrorsMixin,
                      auth_forms.SetPasswordForm):
    pass



class PasswordChangeForm(FloppyWidgetsMixin,
                         NonFieldErrorsMixin,
                         auth_forms.PasswordChangeForm):
    pass
