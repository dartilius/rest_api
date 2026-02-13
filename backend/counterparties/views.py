from uuid import UUID

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiRequest, OpenApiExample
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_404_NOT_FOUND

from counterparties.models import Counterparty, TYPE_FL, TYPE_ORG
from counterparties.serializers import CounterpartiesSerializer, CounterpartiesListSerializer, \
    CreateCounterpartySerializer, CounterpartiesShortSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Пагинированный список Контрагентов",
        description=(
            "Возвращает постраничный список КА. "
            "Использует `CounterpartiesListSerializer`."
        ),
        responses={
            200: OpenApiResponse(
                response=CounterpartiesListSerializer,
                description="Успешное получение списка КА."
            )
        }
    ),

    retrieve=extend_schema(
        summary="Расшифровка КА",
        description="Возвращает полный перечень данных КА по коду 1с или id (UUID)",
        responses={
            200: OpenApiResponse(
                response=CounterpartiesSerializer,
                description="Успешное получение КА."
            )
        }
    ),

    create=extend_schema(
        summary="Создание КА",
        description=(
                "Создает контрагента. "
                "В зависимости от ОПФ требуется различный набор полей.\n\n"
                "ОПФ физлиц: IP, FL, SE\n"
                "ОПФ юрлиц: AO, BF, ZAO, MAU, MP, OAO, OOO, PAO, TCN\n\n"
                "Использует `CreateCounterpartySerializer`."
        ),
        request=CreateCounterpartySerializer,
        responses={
            201: OpenApiResponse(
                response=CounterpartiesShortSerializer,
                description="Контрагент успешно создан"
            )
        },
        examples=[
            # ------ ФИЗЛИЦО ------
            OpenApiExample(
                name="Пример ФизЛицо (FL)",
                summary="Создание Контрагента — ФЛ",
                description="Пример тела запроса для ОПФ FL",
                value={
                    "opf": "FL",
                    "first_name": "Иван",
                    "middle_name": "Иванович",
                    "last_name": "Петров",
                    "contact_persons": ["uuid"],
                    "brands": ["uuid", "uuid"],
                    "description": "Поставщик овощей",
                },
            ),
            # ------ ЮРЛИЦО ------
            OpenApiExample(
                name="Пример ЮрЛицо (OOO)",
                summary="Создание Контрагента — ООО",
                description="Пример тела запроса для ОПФ OOO",
                value={
                    "opf": "OOO",
                    "keyword": "ООО Ромашка",
                    "contact_persons": ["uuid"],
                    "brands": ["uuid"],
                    "inn": "7734567890",
                    "description": "Официальный дилер"
                },
            ),
        ]
    )
)
@extend_schema(tags=["Контрагенты"])
class CounterpartiesViewSet(viewsets.ModelViewSet):
    queryset = Counterparty.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateCounterpartySerializer
        elif self.action == 'list':
            return CounterpartiesListSerializer
        else:
            return CounterpartiesSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_employee:
            return qs
        if user.is_contact_person:
            return qs.filter(contact_persons=user)

        raise NotFound("Страница не найдена!")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        counterparty = serializer.save()
        short = CounterpartiesShortSerializer(counterparty)
        return Response(short.data, status=HTTP_201_CREATED)

    def get_object(self):
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        # Проверяем, валидный ли UUID
        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        # Если UUID — ищем по id
        if is_uuid:
            try:
                counterparty = Counterparty.objects.get(id=identifier)
                return counterparty
            except Counterparty.DoesNotExist:
                raise NotFound("КА не найден.")

        # Если не UUID — ищем по code1c
        try:
            counterparty = Counterparty.objects.get(code1c=identifier)
            return counterparty
        except Counterparty.DoesNotExist:
            raise NotFound("КА не найден.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)

        instance = self.get_object()
        old_opf = instance.opf
        new_opf = request.data.get("opf", old_opf)

        data = request.data

        # Если ОПФ меняется — сперва проверяем, НЕ пустые ли новые данные
        if old_opf != new_opf:

            errors = {}

            # === ЮЛ ===
            if new_opf in TYPE_ORG:
                keyword = data.get("keyword", "").strip()
                inn = data.get("inn", "").strip()

                if not keyword:
                    errors["keyword"] = "Поле обязательно для юридических лиц."

                # if not inn:
                #     errors["inn"] = "ИНН обязателен для юридических лиц."
                if len(inn) != 10:
                    errors["inn"] = "ИНН юридического лица должен содержать 10 цифр."

            # === ФЛ ===
            elif new_opf in TYPE_FL:
                first = data.get("first_name", "").strip()
                last = data.get("last_name", "").strip()
                inn = data.get("inn", "").strip()

                if not first:
                    errors["first_name"] = "Имя обязательно для физического лица."

                if not last:
                    errors["last_name"] = "Фамилия обязательна для физического лица."

                # if not inn:
                #     errors["inn"] = "ИНН обязателен для физического лица."
                if len(inn) != 12:
                    errors["inn"] = "ИНН физического лица должен содержать 12 цифр."

            if errors:
                return Response(
                    {"errors": errors, "detail": "Заполните обязательные поля."},
                    status=400
                )

            # ===== Затирание старых полей =====
            instance.inn = ""

            # ФЛ → ЮЛ
            if old_opf in TYPE_FL and new_opf in TYPE_ORG:
                instance.first_name = ""
                instance.middle_name = ""
                instance.last_name = ""

            # ЮЛ → ФЛ
            elif old_opf in TYPE_ORG and new_opf in TYPE_FL:
                instance.keyword = ""

            instance.opf = new_opf
            instance.save()

        # Далее обычный апдейт сериализатором
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        counterparty = serializer.save()
        short = CounterpartiesShortSerializer(counterparty)

        return Response(short.data, status=HTTP_200_OK)