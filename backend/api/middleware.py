from django.db.utils import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import re
import logging

logger = logging.getLogger(__name__)


class IntegrityMiddleware:
    """
    Обработчик ошибок при записи в БД с поддержкой Django Debug Toolbar
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Полностью пропускаем все запросы, связанные с debug toolbar
        debug_paths = [
            '/__debug__/',
            '/static/debug_toolbar/',
            '/debug_toolbar/',
        ]

        if any(request.path.startswith(path) for path in debug_paths):
            return None

        # Проверяем, не является ли это AJAX запросом от тулбара
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Для AJAX запросов тулбара используем JSON ответ
            if isinstance(exception, IntegrityError):
                return JsonResponse(
                    {'error': str(exception)},
                    status=400
                )
            return None

        if isinstance(exception, IntegrityError):
            err_text = str(exception).lower()

            # Обработка unique constraint ошибок
            if 'unique constraint' in err_text:
                try:
                    # Парсим имя модели
                    model_match = re.search(r'"([^"]+)_([^"]+)"', err_text)
                    if model_match:
                        model_name = model_match.group(1)
                    else:
                        model_name = err_text.split('"')[1].split('_')[0]

                    # Парсим имя поля
                    field_match = re.search(r'\(([^)]+)\)', err_text)
                    field_name = field_match.group(1) if field_match else 'поле'

                    # Создаем ответ с правильными атрибутами
                    response = HttpResponse(
                        f'{model_name} с таким {field_name} уже существует',
                        status=400,
                        content_type='text/plain; charset=utf-8'
                    )

                    # Добавляем атрибуты, необходимые для Debug Toolbar
                    response.render = lambda: response
                    response._has_been_rendered = True

                    # Добавляем заголовки для предотвращения кэширования
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'

                    return response

                except Exception as e:
                    logger.error(f"Error in IntegrityMiddleware: {e}")
                    # Возвращаем общее сообщение об ошибке
                    response = HttpResponse(
                        'Ошибка целостности данных',
                        status=400,
                        content_type='text/plain; charset=utf-8'
                    )
                    response.render = lambda: response
                    response._has_been_rendered = True
                    return response

            # Для других типов IntegrityError пробрасываем исключение
            return None

        return None