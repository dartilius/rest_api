from django.db.utils import IntegrityError
from django.http import HttpResponse


class IntegrityMiddleware:
    """
    Обработчик ошибок при записи в БД.

    Данный обработчик перехватывает IntegrityError, например при попытке
    загрузить файл с уже существующим в базе хешем. Проблема в том, что
    UniqueConstraint не позволяет задать своё сообщение об ошибке на
    данный момент. Пример сообщения благодаря этому костылю:

    file с таким hash уже существует

    Иначе ошибка выглядит так:
    django.db.utils.IntegrityError:
    duplicate key value violates unique constraint "unique_file_hash"
    Key (hash)=(<hash>) already exists.

    Названия модели и поля берутся из возникающей ошибки.
    Проблема была в том, что эта ошибка возвращала статус 500, теперь же 400.

    На случай возникновения этой ошибки по другой причине код попдает в except
    и выводит ошибку как есть.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, IntegrityError):
            err_text = str(exception).lower()
            if 'unique constraint' in err_text:
                model_name = err_text[err_text.index('"')+1:err_text.index('_')]
                field_name = err_text[err_text.index('(') + 1:err_text.index(')')]
                return HttpResponse(
                    f'{model_name} с таким {field_name} уже существует',
                    status=400
                )
            else:
                raise exception
