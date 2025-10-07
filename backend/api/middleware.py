from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
import logging

# Настройка логгера
logger = logging.getLogger(__name__)


class IntegrityMiddleware:
    """
    Middleware для обработки ошибок целостности БД.
    
    Перехватывает IntegrityError и преобразует в понятные
    сообщения об ошибках с соответствующими HTTP статусами.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Обрабатывает исключения IntegrityError.
        
        Args:
            request: HttpRequest объект
            exception: Возникшее исключение
            
        Returns:
            HttpResponse: Ответ с ошибкой или None
        """
        if not isinstance(exception, IntegrityError):
            return None
            
        error_str = str(exception).lower()
        
        # Обработка unique constraint violations
        if 'unique constraint' in error_str:
            return self._handle_unique_violation(error_str)
        
        # Логируем другие IntegrityError для отладки
        logger.warning(f"Unhandled IntegrityError: {error_str}")
        return None

    def _handle_unique_violation(self, error_str):
        """
        Обрабатывает нарушения уникальности.
        
        Args:
            error_str: Текст ошибки
            
        Returns:
            HttpResponse: Ответ с ошибкой 400
        """
        try:
            # Парсим название ограничения
            constraint_start = error_str.find('"') + 1
            constraint_end = error_str.find('"', constraint_start)
            constraint_name = error_str[constraint_start:constraint_end]
            
            # Извлекаем название модели и поля из имени ограничения
            if constraint_name.startswith('unique_'):
                parts = constraint_name.split('_')
                if len(parts) >= 3:
                    model_name = parts[1]  # Название модели
                    field_name = parts[2]  # Название поля
                    
                    return JsonResponse(
                        {
                            'error': f'{model_name} с таким {field_name} уже существует',
                            'code': 'unique_violation'
                        },
                        status=400
                    )
        except (IndexError, ValueError):
            # Если не удалось распарсить, возвращаем общую ошибку
            pass
            
        return JsonResponse(
            {'error': 'Нарушение уникальности данных', 'code': 'integrity_error'},
            status=400
        )
