from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.safestring import mark_safe
from django import forms

from base import actions
from base import widgets as base_widgets


register = Library()

################################
# FORM RENDERING
################################

@register.simple_tag
def render_field(bound, label=None):
    """ This template tag renders the passed in field in bootstrap horizontal form format. """

    # shortcut for hidden fields
    if bound.is_hidden:
        return '<div class="hidden">{widget}</div>'.format(widget=bound)

    # set our css classes
    classes = ['form-group']

    # setup the required indicator
    if bound.field.required:
        required_indicator = '<span class="required-indicator"' \
                             ' title="This Field is Required">*</span>'
    else:
        required_indicator = '<span class="required-indicator">&nbsp;</span>'

    if bound.errors:
        classes.append('error')

    # setup the label
    field_label = label or bound.label
    if not field_label.strip():
        final_label = ' '
    elif (isinstance(bound.field.widget, forms.widgets.CheckboxInput)):
        final_label = '{label}{required}'.format(label=field_label, required=required_indicator)
    else:
        final_label = '{label}:{required}'.format(label=field_label, required=required_indicator)

    # render the row
    ctx = {
        'name': bound.name,
        'classes': ' '.join(classes),
        'label': final_label,
        'widget': bound,
        'error': bound.errors,
    }

    template = '<div id="div_{name}" class="{classes}"><label class="col-sm-2 control-label" for="id_{name}">{label}</label><div class="col-sm-8">{widget}<span class="help-block">{error}</span></div></div>'
    checkbox_template = '<div id="div_{name}" class="{classes}"><label class="col-sm-9 col-sm-offset-1 checkbox">{widget} {label}</label><span class="help-block">{error}</span></div>'
    radio_template = '<div id="div_{name}" class="{classes}"><label class="col-sm-9 col-sm-offset-1 radio">{widget}</label><span class="help-block">{error}</span></div>'
    if (isinstance(bound.field.widget, forms.widgets.CheckboxInput)):
        return mark_safe(checkbox_template.format(**ctx))
    elif isinstance(bound.field.widget, forms.widgets.RadioSelect):
        return mark_safe(radio_template.format(**ctx))
    return mark_safe(template.format(**ctx))


@register.simple_tag
def render_form(form, in_widget=False, show_legend=True):
    """ This template tag renders a form using fieldsets defined on a form, or simply all the fields
        on the form if there is no defined fieldsets on the form.

        Use the tag like this:
        {% render_form form %}

        Where "form" is the form to be rendered.

        Example on how to build the fieldsets parameter
        fieldsets = [
            {"id": "personal", "fields":['name','gender'], "legend":"Personal Data", "title": ".."},
            {"id": "address": , "fields":["street", "number", "city", "zip"], "legend":"Address"},
         }
    """
    def get_visible_inputs(form):
        visible_inputs = []
        for name, field in form.fields.items():
            if not isinstance(field.widget, field.hidden_widget):
                visible_inputs.append(field)
        return visible_inputs

    # helper for rendering a list of fields
    def get_fields_html(field_names, form):
        fields_html = []
        for field_name in field_names:
            if field_name in form.fields:
                fields_html.append(render_field(form[field_name]))
        return ''.join(fields_html)

    # helper for rendering fieldsets
    def get_fieldsets_html(fieldsets, form, show_legend):
        fieldset_html = '<fieldset id="{id}">{legend}' \
                        '{title}<div>{fields}</div></fieldset>'

        fieldsets_html = []
        for fieldset in fieldsets:
            legend = ''
            if show_legend:
                legend = "<legend>{legend}</legend>".format(legend=fieldset.get('legend', ''))
            title = fieldset.get('title', '')
            if title:
                title = '<p class="title">{title}</p>'.format(title=title)
            ctx = {
                'id': fieldset.get('id', ''),
                'legend': legend,
                'fields': get_fields_html(fieldset.get('fields', form.fields.keys()), form),
                'title': title,
            }
            fieldsets_html.append(fieldset_html.format(**ctx))

        return ''.join(fieldsets_html)

    errors = render_form_errors_helper(form)

    # see if we have a meta class
    exclude_names = []
    if hasattr(form, 'Meta'):
        meta = form.Meta

        # meta class contains fieldsets
        if hasattr(meta, 'fieldsets'):
            if in_widget:
                fieldset_string = '{errors}<div class="fieldset-container">{fieldsets}</div>'
            else:
                fieldset_string = '{errors}{fieldsets}'
            return fieldset_string.format(errors=errors, fieldsets=get_fieldsets_html(meta.fieldsets, form, show_legend))

        # no fieldsets in meta see if we have excludes
        if hasattr(meta, 'excludes'):
            exclude_names = meta.excludes

    # get the field list and remove the excluded fields
    field_names = form.fields.keys()
    field_names = filter(lambda x: x not in exclude_names, field_names)
    if in_widget:
        form_string = '{errors}<div class="fieldset-container"><fieldset><div>{fields}</div></fieldset></div>'
    else:
        form_string = '{errors}<fieldset><div>{fields}</div></fieldset>'
    return mark_safe(form_string.format(errors=errors, fields=get_fields_html(field_names, form)))


@register.simple_tag
def render_form_errors(form, fieldsets=None):
    return mark_safe(render_form_errors_helper(form))


def render_form_errors_helper(form):
    rendered_form_errors = ''
    error_base = "<div class=\"alert alert-error\"><strong>There were errors with your form submission." \
                 " Please correct to continue.</strong> {messages} </div>"

    if hasattr(form, 'show_no_base_error'):
        rendered_form_errors = "<div class=\"error_notice_dialog\">{errors}</div>".format(errors=unicode(form.non_field_errors()))
    elif form.non_field_errors():
        error_messages = unicode(form.non_field_errors())
        rendered_form_errors = error_base.format(messages=error_messages)
    elif form.errors:
        rendered_form_errors = error_base.format(messages="")
    return rendered_form_errors


@register.simple_tag(takes_context=True)
def render_form_widget(context, form, title=None, show_legend=False, icon='icon-plus', desc=""):
    if hasattr(form, 'Meta') and not title:
        meta = form.Meta

        # meta class contains fieldsets
        if hasattr(meta, 'fieldsets'):
            title = meta.fieldsets[0].get('legend', "Title")

    context.update({
        'widget_content': mark_safe(render_form(form, in_widget=True, show_legend=show_legend)),
        'widget_title': title,
        'widget_icon': icon,
        'widget_description': desc,
    })
    return mark_safe(actions.render_template(None, 'includes/widget_box.html', context))


@register.filter
def is_list(value):
    """
    Check if a variable is a list.
    """
    if type(value) == list:
        return True
    return False


@register.simple_tag(takes_context=True)
def render_form_controlbox(context, style=""):
    context['button_style'] = style
    return mark_safe(actions.render_template(None, 'includes/form_controlbox.html', context))


@register.simple_tag
def render_widget_table(data):
    output = '<table class="table table-bordered">'
    output += '<thead>'
    for header in data.get('headers', None):
        output += '<th>{header}</th>'.format(header=header)
    output += '</thead>'

    for row in data.get('rows', None):
        output += '<tr>'
        for cell in row:
            output += '<td>{cell}</td>'.format(cell=cell)
        output += '</tr>'
    output += '</table>'
    output += '</div>'

    return output


@register.simple_tag
def render_widget(widget_data):
    widget_output = '<div class="widget-box"><div class="widget-title">'

    icon = widget_data.get('icon', None)
    if icon:
        widget_output += '<span class="icon"><i class="fa {icon}"></i></span>'.format(icon=icon)

    widget_output += '<h5>{title}</h5>'.format(title=widget_data.get('title', None))

    buttons = widget_data.get('buttons', None)
    if buttons:
        widget_output += '<div class="buttons">'
        for button in buttons:
            widget_output += '<a href="{link}" class="btn btn-mini"> <i class="fa {icon}"></i>{button}</a>'.format(button)
        widget_output += '</div>'

    widget_output += '</div>'

    table = widget_data.get('table', None)
    if table:
        widget_output += '<div class="widget-content nopadding">{table}</div></div>'.format(table=render_widget_table(table))
    else:
        widget_output += '<div class="widget-content">{data}'.format(data=widget_data.get('content', ""))

    return mark_safe(widget_output)


@register.simple_tag
def render_widget_bottom():
    return mark_safe('</div></div>')


@register.simple_tag
def render_account_type(participant):
    if participant.is_red:
        return mark_safe('<span class="text-danger">Red</span>')
    elif participant.is_green:
        return mark_safe('<span class="text-success">Green</span>')
    return mark_safe('<span class="text-primary">Blue</span>')


@register.simple_tag
def render_email_archive(archive, show_audience=False):
    output = '<div class="list-group">'

    template = '<a class="list-group-item" href="{url}"><h4 class=list-group-item-heading>{subject}</h4>{content}</a>'
    for email in archive:
        url = reverse('archive-email', args=[email.id])
        subject = email.subject

        content = '<p class="list-group-item-text clearfix">Sent {sent} {audience}</p>'

        if show_audience:
            audience = '<span class="pull-right badge">{}</span>'.format(email.get_audience_display())
        else:
            audience = ""

        content = content.format(sent=email.send_time.strftime('%x %I:%M %p'), audience=audience)

        output += template.format(subject=subject, url=url, content=content)

    output += '</div>'
    return mark_safe(output)


@register.simple_tag
def render_rules_version():
    output = '<a href="{url}">Rules {version}</a>'
    version = actions.get_global_setting('rules_version')
    url = settings.RULES_URL.format(version=version)

    return mark_safe(output.format(url=url, version=version))