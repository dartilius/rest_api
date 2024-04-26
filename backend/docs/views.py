from django.shortcuts import render
from templates import *


def docs(request):
    return render(request, "redoc.html")


def openapi_scheme(request):
    return render(request, "openapi-schema.yml")
