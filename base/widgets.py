from django import forms
from django.forms.utils import flatatt
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

class ReadonlyWidget(forms.widgets.Widget):

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        value = force_unicode(value)
        final_attrs = forms.util.flatatt(self.build_attrs(attrs, name=name, value=value))
        return mark_safe(u'<input type="hidden"{attrs} /><span class="field">{value}</span>'.format(attrs=final_attrs, value=value))

    def _has_changed(self, initial, data):
        return False


class DateInput(forms.widgets.DateInput):
    """
    Widget for showing a hint title in the field.
    """
    def __init__(self, attrs=None, title=None, format=None):
        if not format:
            format = "%m/%d/%Y"
        forms.widgets.DateInput.__init__(self, attrs, format)

    def render(self, name, value, attrs=None):
        date_attrs = self.build_attrs(attrs)
        date_attrs['class'] = 'datepicker-input'
        input = forms.widgets.DateInput.render(self, name, value, date_attrs)
        return mark_safe(input)


class DateTimeInput(forms.widgets.SplitDateTimeWidget):

    def __init__(self, attrs=None, date_format=None, time_format=None, initial=None):
        if attrs is None:
            attrs = {}
        date_attrs = attrs.copy()
        time_attrs = attrs.copy()
        time_attrs['class'] = 'datepicker-input-trailer'
        if initial:
            date_attrs['value'] = initial.date()
            time_attrs['value'] = initial.time()
        else:
            date_attrs['placeholder'] = 'MM/DD/YYYY'
            time_attrs['placeholder'] = 'HH:MM (24hr)'
        widgets = (DateInput(attrs=date_attrs, format=date_format),
                   forms.widgets.TimeInput(attrs=time_attrs, format=time_format))
        super(forms.widgets.SplitDateTimeWidget, self).__init__(widgets, attrs)
