from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PageLimitPagination(PageNumberPagination):
    """
    Кастомная пагинация с поддержкой лимита через параметр запроса.
    
    Наследает от PageNumberPagination и добавляет:
    - Параметр 'limit' для управления размером страницы
    - Расширенный ответ с дополнительными метаданными
    """
    
    page_size_query_param = 'limit'
    max_page_size = 100  # Защита от слишком больших страниц

    def get_paginated_response(self, data, **kwargs):
        """
        Формирует ответ с пагинацией.
        
        Args:
            data: Данные для текущей страницы
            **kwargs: Дополнительные метаданные
            
        Returns:
            Response: Ответ с пагинационными метаданными
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            **kwargs,
        })
