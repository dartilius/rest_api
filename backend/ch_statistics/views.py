from django.shortcuts import render


def docs(request):
    return render(request, 'redoc.html')


def openapi(request):
    return render(request, 'openapi-schema.yml')
