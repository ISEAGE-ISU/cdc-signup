from django import forms
from django.forms.util import flatatt
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
