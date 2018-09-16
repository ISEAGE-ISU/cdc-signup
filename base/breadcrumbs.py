from django.core import urlresolvers
from django import http
from django.utils.html import format_html
from urlparse import urljoin


class Breadcrumb(object):
    link = ""
    text = ""
    active = False

    def __init__(self, link, text, active):
        self.link = link
        self.text = text
        self.active = active

    def render(self):
        if self.active:
            return format_html('<a href="{link}" class="current">{text}</a>', link=self.link, text=self.text)
        else:
            return format_html('<a href="{link}">{text}</a>', link=self.link, text=self.text)


def render_breadcrumbs(path, context):
    breadcrumbs = create_breadcrumbs(path, context)

    html = ""
    for bread in breadcrumbs:
        html += bread.render()
    return html


def create_breadcrumbs(path, context):
    counter = 20
    breadcrumbs = []

    if '?' in path:
        path = path.split('?')[0]
    url = path

    while True:
        counter -= 1
        if counter < 1:
            break

        # Try to resolve the url to a view
        view = None
        try:
            # Stack Overview answer:
            # http://stackoverflow.com/questions/5749075/django-get-generic-view-class-from-url-name
            resolver_match = urlresolvers.resolve(url)
            func = resolver_match.func
            view_args = resolver_match.args
            view_kwargs = resolver_match.kwargs
            module = func.__module__
            view_name = func.__name__
            view = get_class('{0}.{1}'.format(module, view_name))
        # Couldn't resolve the url
        except http.Http404 as e:
            pass

        # We have a valid view
        else:
            text = getattr(view, 'breadcrumb', None)
            if callable(text):
                text = text(context, *view_args, **view_kwargs)

            if text:
                breadcrumbs.append(Breadcrumb(url, text, url == path))

        if url == '/':
            break

        url = urljoin(url, '..')

    breadcrumbs.reverse()
    return breadcrumbs


# This is fairly janky.  Found it at stack overflow.
# http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m
