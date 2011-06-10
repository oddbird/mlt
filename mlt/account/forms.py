from django.contrib.auth import forms as auth_forms

import floppyforms as forms

from ..core.forms import (
    LabelPlaceholdersMixin, FloppyWidgetsMixin, NonFieldErrorsMixin)



class AuthenticationForm(LabelPlaceholdersMixin,
                         FloppyWidgetsMixin,
                         NonFieldErrorsMixin,
                         auth_forms.AuthenticationForm):
    pass



class PasswordResetForm(LabelPlaceholdersMixin,
                        FloppyWidgetsMixin,
                        NonFieldErrorsMixin,
                        auth_forms.PasswordResetForm):
    widget_classes = {"email": forms.EmailInput}



class SetPasswordForm(LabelPlaceholdersMixin,
                      FloppyWidgetsMixin,
                      NonFieldErrorsMixin,
                      auth_forms.SetPasswordForm):
    pass



class PasswordChangeForm(LabelPlaceholdersMixin,
                         FloppyWidgetsMixin,
                         NonFieldErrorsMixin,
                         auth_forms.PasswordChangeForm):
    pass
