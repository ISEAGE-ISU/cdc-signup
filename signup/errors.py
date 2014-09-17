from django.shortcuts import render
import base


def error403(request):
    context = base.get_context(request)
    context['page_title'] = "Forbidden"
    return render(request, '403.html', context_instance=context, status=403)


def error404(request):
    context = base.get_context(request)
    context['page_title'] = "Not Found"
    return render(request, '404.html', context_instance=context, status=404)


def error500(request):
    context = {
        'page_title': "Internal Server Error"
    }
    return render(request, '500.html', dictionary=context, status=500)
