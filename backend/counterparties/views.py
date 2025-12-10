from uuid import UUID

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiRequest, OpenApiExample
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

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
    lookup_field = "id_or_code1c"
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCounterpartySerializer
        elif self.action == 'list':
            return CounterpartiesListSerializer
        else:
            return CounterpartiesSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        counterparty = serializer.save()
        short = CounterpartiesShortSerializer(counterparty)
        return Response(short.data, status=HTTP_201_CREATED)

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            counterparty = Counterparty.active.get(id=uuid_obj)
            if counterparty.is_active is False:
                raise NotFound("КА не найден.")
            return counterparty
        except (ValueError, Counterparty.DoesNotExist):
            pass

        # пробуем code1c
        try:
            counterparty = Counterparty.active.get(code1c=identifier)
            if counterparty.is_deleted:
                raise NotFound("КА не найден.")
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

                if not inn:
                    errors["inn"] = "ИНН обязателен для юридических лиц."
                elif len(inn) != 10:
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

                if not inn:
                    errors["inn"] = "ИНН обязателен для физического лица."
                elif len(inn) != 12:
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

# class CounterpartiesViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     http_method_names = ["get", "post", "patch", "delete"]
#     queryset = Counterparty.active.all()
#     lookup_field = "id_or_code1c"
#
#     def get_queryset(self):
#         user = self.request.user
#
#         if not user.is_authenticated:
#             return Counterparty.objects.none()
#
#         is_broadcast = user.is_contact_person_broadcast
#         is_ad = user.is_contact_person_ad
#         is_admin = (
#                 user.is_admin
#                 or user.is_superuser
#                 or user.is_ordinary
#                 or user.is_manager
#         )
#
#         qs = Counterparty.objects.all().order_by('id')
#
#         if is_broadcast or is_ad:
#             user_counterparties = Counterparty.objects.filter(contact_persons=user)
#
#             qs = qs.filter(
#                 Q(id__in=user_counterparties.values_list('id', flat=True))
#             ).distinct()
#
#         elif is_admin:
#             pass  # админы видят всех
#
#         else:
#             qs = Counterparty.objects.none()
#
#         return qs
#
#     def get_serializer_class(self):
#         if self.action == "create":
#             return CounterpartiesCreateSerializer
#         return CounterpartiesSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         counterparties = serializer.save()
#         short = CounterpartiesShortSerializer(counterparties)
#         return Response(short.data, status=HTTP_201_CREATED)
#
#     def destroy(self, request, *args, **kwargs):
#
#         counterparties = self.get_object()
#         counterparties.delete()
#         return Response(status=HTTP_204_NO_CONTENT)
#
#     def get_object(self):
#
#         identifier = self.kwargs.get(self.lookup_field)
#         if not identifier:
#             raise NotFound("Не указан идентификатор контрагента.")
#
#         # пробуем UUID
#         try:
#             uuid_obj = UUID(str(identifier))
#             counterparty = Counterparty.objects.get(id=uuid_obj)
#             if not counterparty.is_active:
#                 raise NotFound("Контрагент не найден.")
#             return counterparty
#         except (ValueError, Counterparty.DoesNotExist):
#             pass
#
#         # пробуем code1c
#         try:
#             counterparty = Counterparty.objects.get(code1c=identifier)
#             if not counterparty.is_active:
#                 raise NotFound("Контрагент не найден.")
#             return counterparty
#         except Counterparty.DoesNotExist:
#             raise NotFound("Контрагент не найден.")
#
#     @action(detail=True, methods=["delete"], url_path="cp/remove/(?P<user_id>[^/.]+)")
#     def remove_contact_person(self, request, id_or_code1c=None, user_id=None):
#         counterparty = self.get_object()
#
#         try:
#             user = CustomUser.objects.get(id=user_id)
#         except CustomUser.DoesNotExist:
#             return Response({"detail": "User not found"}, status=404)
#
#         counterparty.contact_persons.remove(user)
#         return Response({"detail": "removed"}, status=200)
