from django.contrib.auth import forms as auth_forms



class LabelPlaceholdersMixin(object):
    def __init__(self, *args, **kwargs):
        super(LabelPlaceholdersMixin, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", field.label)



class AuthenticationForm(LabelPlaceholdersMixin, auth_forms.AuthenticationForm):
    pass



class PasswordResetForm(LabelPlaceholdersMixin, auth_forms.PasswordResetForm):
    pass



class SetPasswordForm(LabelPlaceholdersMixin, auth_forms.SetPasswordForm):
    pass



class PasswordChangeForm(LabelPlaceholdersMixin, auth_forms.PasswordChangeForm):
    pass
