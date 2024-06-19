from django.db.utils import IntegrityError
from django.http import JsonResponse, HttpResponse


class IntegrityMiddleware:
    """
    Обработчик ошибок при записи в БД.

    Данный обработчик костыльным образом прерывает процесс создания файла или
    другого объекта, если у него есть поле, уникальность которого была нарушена.
    Например при попытке загрузить на сервер один и тот же файл дважды
    через админ-панель ответ будет таким:

    IntegrityError
    Model: file
    Attribute: hash

    Названия модели и поля берутся из возникающей ошибки.
    Проблема была в том, что эта ошибка возникает скрытно и видно её только
    в логах сервера.

    На случай возникновения этой ошибки по другой причине код попдает в except
    и выводит ошибку как есть.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, IntegrityError):
            try:
                err_text = str(exception)
                model_name = err_text[err_text.index('"')+1:err_text.index('_')]
                attribute_name = err_text[
                                 err_text.index('Key')+5:err_text.index(')=(')
                                 ]
                response_content = (
                    f"""
                        <html>
                        <head><title>Integrity Error</title></head>
                        <body>
                            <h1>Integrity Error</h1>
                            <p>Model: {model_name}</p>
                            <p>Attribute: {attribute_name}</p>
                            <button onclick="history.back()">Go Back</button>
                        </body>
                        </html>
                    """)
                return HttpResponse(
                    response_content, content_type="text/html", status=400
                )
            except ValueError:
                pass
