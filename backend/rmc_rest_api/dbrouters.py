from clickhouse_backend.models import ClickhouseModel
from django.conf import settings


def get_subclasses(class_):
    """
    Рекурсивно получает все подклассы указанного класса.
    
    Args:
        class_: Базовый класс для поиска подклассов
        
    Returns:
        list: Список всех неабстрактных подклассов
    """
    classes = class_.__subclasses__()
    index = 0
    while index < len(classes):
        classes.extend(classes[index].__subclasses__())
        index += 1

    return list(set(classes))


class ClickHouseRouter:
    """
    Router для автоматического направления моделей ClickHouse в соответствующую БД.
    
    Автоматически определяет все модели, унаследованные от ClickhouseModel,
    и направляет их операции в базу данных 'clickhouse'.
    """

    def __init__(self):
        """
        Инициализирует router, предварительно загружая все модели ClickHouse.
        """
        self.route_model_names = set()
        # Отложенная загрузка моделей при первом обращении
        self._models_loaded = False
        
    def _load_models(self):
        """
        Загружает все модели ClickHouse при первом обращении к router.
        """
        if self._models_loaded:
            return
            
        try:
            for model in get_subclasses(ClickhouseModel):
                if model._meta.abstract:
                    continue
                self.route_model_names.add(model._meta.label_lower)
            self._models_loaded = True
        except Exception as e:
            # В случае ошибки загрузки моделей логируем и продолжаем
            if settings.DEBUG:
                print(f"Warning: Error loading ClickHouse models: {e}")
            self._models_loaded = True

    def db_for_read(self, model, **hints):
        """
        Определяет базу данных для операций чтения.
        
        Args:
            model: Модель Django
            hints: Дополнительные подсказки
            
        Returns:
            str: Имя базы данных или None для использования по умолчанию
        """
        if not self._models_loaded:
            self._load_models()
            
        if (model._meta.label_lower in self.route_model_names
                or hints.get("clickhouse")):
            return "clickhouse"
        return None

    def db_for_write(self, model, **hints):
        """
        Определяет базу данных для операций записи.
        
        Args:
            model: Модель Django
            hints: Дополнительные подсказки
            
        Returns:
            str: Имя базы данных или None для использования по умолчанию
        """
        if not self._models_loaded:
            self._load_models()
            
        if (model._meta.label_lower in self.route_model_names
                or hints.get("clickhouse")):
            return "clickhouse"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Определяет, разрешены ли миграции для указанной базы данных.
        
        Args:
            db: Имя базы данных
            app_label: Имя приложения
            model_name: Имя модели (опционально)
            hints: Дополнительные подсказки
            
        Returns:
            bool: Разрешены ли миграции
        """
        if not self._models_loaded:
            self._load_models()
            
        full_model_name = f"{app_label}.{model_name}" if model_name else None
        
        if (full_model_name and full_model_name in self.route_model_names
                or hints.get("clickhouse")):
            return db == "clickhouse"
        elif db == "clickhouse":
            # В clickhouse разрешаем только миграции для ClickHouse моделей
            return False
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Определяет, разрешены ли отношения между объектами.
        
        Для ClickHouse отношений между разными базами данных не поддерживается.
        
        Args:
            obj1: Первый объект
            obj2: Второй объект
            hints: Дополнительные подсказки
            
        Returns:
            bool: Разрешено ли отношение
        """
        if not self._models_loaded:
            self._load_models()
            
        # Определяем, принадлежат ли объекты к ClickHouse
        obj1_clickhouse = (obj1._meta.label_lower in self.route_model_names 
                          or hints.get("clickhouse"))
        obj2_clickhouse = (obj2._meta.label_lower in self.route_model_names 
                          or hints.get("clickhouse"))
        
        # Отношения между разными базами данных не поддерживаются
        if obj1_clickhouse and not obj2_clickhouse:
            return False
        if not obj1_clickhouse and obj2_clickhouse:
            return False
            
        return None
