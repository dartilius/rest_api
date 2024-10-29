import pytest

from django.shortcuts import get_object_or_404
from itertools import chain
from uuid import UUID

from nomenclatures.models import Nomenclature


@pytest.mark.django_db
class TestOrders:

    def test_chain_and_id(self, nomenclature, adorder, bgorder):
        nom = get_object_or_404(Nomenclature, id=str(nomenclature.id))
        orders_list = chain(
            nom.adorders.filter(status__in=[0, 1]),
            nom.bgorders.filter(status__in=[0, 1])
        )

        for order in orders_list:
            assert isinstance(order.id, UUID)
