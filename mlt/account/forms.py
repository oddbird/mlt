from django.contrib.auth import forms as auth_forms

import floppyforms as forms



class LabelPlaceholdersMixin(object):
    """
    Form mixin class to give all widgets a "placeholder" attribute the same as
    their label.

    """
    def __init__(self, *args, **kwargs):
        super(LabelPlaceholdersMixin, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", field.label)


class FloppyWidgetsMixin(object):
    """
    Form mixin class to replace standard Django form widgets with the
    floppyforms HTML5 template-driven widget equivalent.

    Also looks up a possible explicit widget-class override in
    ``self.widget_classes``.

    """
    widget_classes = {}

    def __init__(self, *args, **kwargs):
        super(FloppyWidgetsMixin, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            widget = field.widget
            new = None
            if fieldname in self.widget_classes:
                new = self.widget_classes[fieldname](widget.attrs)
            else:
                floppy_class = getattr(forms, widget.__class__.__name__, None)
                if floppy_class is not None:
                    new = floppy_class(widget.attrs)
            if new is not None:
                new.is_required = widget.is_required
                field.widget = new



class AuthenticationForm(LabelPlaceholdersMixin,
                         FloppyWidgetsMixin,
                         auth_forms.AuthenticationForm):
    pass



class PasswordResetForm(LabelPlaceholdersMixin,
                        FloppyWidgetsMixin,
                        auth_forms.PasswordResetForm):
    widget_classes = {"email": forms.EmailInput}



class SetPasswordForm(LabelPlaceholdersMixin,
                      FloppyWidgetsMixin,
                      auth_forms.SetPasswordForm):
    pass



class PasswordChangeForm(LabelPlaceholdersMixin,
                         FloppyWidgetsMixin,
                         auth_forms.PasswordChangeForm):
    pass
