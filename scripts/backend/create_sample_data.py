import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rmc_rest_api.settings')
django.setup()

from brands.models import Brand
from addresses.models import Address
from nomenclatures.models import Nomenclature, NomenclatureAddress


def make_settings():
    # минимальные валидные настройки для всех дней
    default = {
        'worktime': '09:00:00-18:00:00',
        'default_volume': [50, 50, 50, 50]
    }
    return {d: default for d in ['mon','tue','wed','thu','fri','sat','sun']}


def main():
    created = {'brands': [], 'addresses': [], 'nomenclatures': []}

    brand, _ = Brand.objects.get_or_create(name='ExampleBrand')
    created['brands'].append(str(brand.id))

    # создаём несколько адресов (минимальный набор полей)
    a1 = Address.objects.create(index='123456', microdistrict='MD1', coordinates='55.0,37.0')
    a2 = Address.objects.create(index='234567', microdistrict='MD2', coordinates='56.0,38.0')
    a3 = Address.objects.create(index='345678', microdistrict='MD3', coordinates='57.0,39.0')
    created['addresses'].extend([str(a1.id), str(a2.id), str(a3.id)])

    # создаём номенклатуры и привязываем адреса
    n1 = Nomenclature.objects.create(name='Nomen1', version='v1', settings=make_settings())
    NomenclatureAddress.objects.update_or_create(nomenclature=n1, defaults={'address': a1})

    n2 = Nomenclature.objects.create(name='Nomen2', version='v1', settings=make_settings(), brand=brand)
    NomenclatureAddress.objects.update_or_create(nomenclature=n2, defaults={'address': a2})

    n3 = Nomenclature.objects.create(name='Nomen3', version='v2', settings=make_settings())
    # не привязываем адрес к третьей, чтобы было покрытие

    created['nomenclatures'].extend([str(n1.id), str(n2.id), str(n3.id)])

    print(json.dumps(created, ensure_ascii=False))


if __name__ == '__main__':
    main()
