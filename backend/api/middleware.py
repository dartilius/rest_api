from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse


class IntegrityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, IntegrityError):
            err_text = str(exception)
            model_name = err_text[err_text.index('"')+1:err_text.index('_')]
            attribute_name = err_text[
                             err_text.index('Key')+5:err_text.index(')=(')
                             ]

            return JsonResponse({
                'IntegrityError': (model_name, attribute_name)
            })
