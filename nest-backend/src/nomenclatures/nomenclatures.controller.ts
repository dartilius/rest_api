import { Body, Controller, Get, Header, HttpCode, Param, Post, Query } from '@nestjs/common';
import { ApiBadRequestResponse, ApiBody, ApiNotFoundResponse, ApiOkResponse, ApiOperation, ApiParam, ApiTags } from '@nestjs/swagger';
import { ApiErrorResponseDto } from '../common/http/api-error.dto';
import { NomenclatureFiltersDto, NomenclatureMapQueryDto, NomenclatureQueryDto } from './dto/nomenclature-query.dto';
import { NomenclatureDetailDto, NomenclatureFilterOptionsDto, NomenclatureMapResponseDto, NomenclaturesListResponseDto } from './dto/nomenclature-response.dto';
import { NomenclaturesService } from './nomenclatures.service';
import { PublicCacheService } from '../common/cache/public-cache.service';

const PUBLIC_CACHE_CONTROL = 'public, max-age=60, s-maxage=300';

@ApiTags('Nomenclatures')
@Controller('nomenclatures')
export class NomenclaturesController {
  constructor(
    private readonly nomenclaturesService: NomenclaturesService,
    private readonly publicCacheService: PublicCacheService,
  ) {}

  @Get()
  @HttpCode(200)
  @Header('Cache-Control', PUBLIC_CACHE_CONTROL)
  @ApiOperation({
    summary: 'Каталог номенклатур / List public nomenclatures',
    description: 'Поддерживает фильтры через query string и пагинацию. Массивы можно передать повторяющимися параметрами или через запятую: `brandIds=a&brandIds=b` либо `brandIds=a,b`. / Supports query-string filters and pagination.',
  })
  @ApiOkResponse({
    type: NomenclaturesListResponseDto,
    example: {
      data: [{
        id: '00000000-0000-4000-8000-000000000020',
        brand: { id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', logoUrl: null },
        exterior: null,
        address: { name: 'г. Красноярск, ул. Мира, 5', coordinates: { latitude: '56.010', longitude: '92.870' } },
        typeOfPlace: { id: '00000000-0000-4000-8000-000000000030', name: 'Торговый центр', abbreviation: 'ТЦ' },
        pricePerMonth: '1250.00', slotsPerHour: '2', oldCatalogSlug: 'demo-brand-krasnoyarsk',
      }],
      pagination: { total: 1, limit: 24, offset: 0 },
    },
  })
  @ApiBadRequestResponse({ type: ApiErrorResponseDto, description: 'Ошибка в параметрах фильтра / Invalid filter parameters.', example: { error: { code: 'INVALID_PRICE_RANGE', message: 'priceFrom must not exceed priceTo.' } } })
  list(@Query() query: NomenclatureQueryDto): Promise<NomenclaturesListResponseDto> {
    return this.publicCacheService.getOrSet('nomenclatures:list', query, () => this.nomenclaturesService.list(query));
  }

  @Post('filter-options')
  @HttpCode(200)
  @Header('Cache-Control', PUBLIC_CACHE_CONTROL)
  @ApiOperation({
    summary: 'Фасеты каталога / Get contextual catalogue filter options',
    description: 'Принимает JSON-фильтры без `ordering`, `limit` и `offset`; для каждого фасета его собственный фильтр исключается. / Accepts JSON filters without pagination; each facet excludes its own filter.',
  })
  @ApiBody({
    type: NomenclatureFiltersDto,
    examples: {
      catalogueFilters: {
        summary: 'Фильтр каталога / Catalogue filters',
        value: { citySlug: 'krasnoyarsk', brandIds: ['00000000-0000-4000-8000-000000000010'], contentTypes: ['audio', 'video'], priceFrom: '1000.00', priceTo: '5000.00', hasFacade: true },
      },
    },
  })
  @ApiOkResponse({
    type: NomenclatureFilterOptionsDto,
    example: {
      brands: [{ id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', count: 3 }],
      typesOfPlace: [{ id: '00000000-0000-4000-8000-000000000030', name: 'Торговый центр', count: 3 }],
      cities: [{ slug: 'krasnoyarsk', name: 'Красноярск', count: 3 }],
      contentTypes: [{ value: 'audio', count: 2 }], versions: [{ value: 'v2', count: 3 }], timezones: [{ value: 'Asia/Krasnoyarsk', count: 3 }], statuses: [{ value: '1', count: 3 }], hasFacade: [{ value: true, count: 2 }, { value: false, count: 1 }], price: { min: '1000.00', max: '5000.00' },
    },
  })
  @ApiBadRequestResponse({ type: ApiErrorResponseDto, description: 'Ошибка в JSON-фильтре / Invalid JSON filters.' })
  filterOptions(@Body() filters: NomenclatureFiltersDto): Promise<NomenclatureFilterOptionsDto> {
    return this.publicCacheService.getOrSet('nomenclatures:filter-options', filters, () => this.nomenclaturesService.filterOptions(filters));
  }

  @Post('map')
  @HttpCode(200)
  @Header('Cache-Control', PUBLIC_CACHE_CONTROL)
  @ApiOperation({ summary: 'Точки на карте / Get public nomenclature map points', description: 'Принимает те же JSON-фильтры, что и фасеты, и возвращает не более 1000 точек. Параметр `limit` управляет числом точек. / Uses the same JSON filters as facets and returns at most 1000 points; `limit` controls the result size.' })
  @ApiBody({
    type: NomenclatureMapQueryDto,
    examples: { mapFilters: { summary: 'Точки в городе / Points in a city', value: { citySlug: 'krasnoyarsk', hasFacade: true, limit: 500 } } },
  })
  @ApiOkResponse({
    type: NomenclatureMapResponseDto,
    example: {
      count: 1,
      results: [{ id: '00000000-0000-4000-8000-000000000020', name: 'ТЦ Demo Brand, г. Красноярск, ул. Мира, 5', coordinates: { latitude: '56.010', longitude: '92.870' }, typeOfPlace: { id: '00000000-0000-4000-8000-000000000030', name: 'Торговый центр', abbreviation: 'ТЦ' }, brand: { id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', logoUrl: null }, facade: null, perDay: 24, perHour: '2', oldCatalogSlug: 'demo-brand-krasnoyarsk' }],
    },
  })
  @ApiBadRequestResponse({ type: ApiErrorResponseDto, description: 'Ошибка в JSON-фильтре / Invalid JSON filters.' })
  map(@Body() filters: NomenclatureMapQueryDto): Promise<NomenclatureMapResponseDto> {
    return this.publicCacheService.getOrSet('nomenclatures:map', filters, () => this.nomenclaturesService.map(filters));
  }

  @Get(':identifier')
  @HttpCode(200)
  @Header('Cache-Control', PUBLIC_CACHE_CONTROL)
  @ApiOperation({ summary: 'Номенклатура по идентификатору / Get public nomenclature by identifier' })
  @ApiParam({ name: 'identifier', description: 'UUID, код 1С или legacy slug каталога / UUID, 1C code, or legacy catalogue slug.', example: 'demo-brand-krasnoyarsk' })
  @ApiOkResponse({
    type: NomenclatureDetailDto,
    example: {
      id: '00000000-0000-4000-8000-000000000020', brand: { id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', logoUrl: null }, exterior: null,
      address: { name: 'г. Красноярск, ул. Мира, 5', fullAddress: 'Красноярский край, г. Красноярск, ул. Мира, д. 5', coordinates: { latitude: '56.010', longitude: '92.870' } },
      typeOfPlace: { id: '00000000-0000-4000-8000-000000000030', name: 'Торговый центр', abbreviation: 'ТЦ' }, pricePerMonth: '1250.00', slotsPerHour: '2', oldCatalogSlug: 'demo-brand-krasnoyarsk', description: 'Демонстрационная поверхность / Demo placement.', contentType: 'audio', worktimeStart: '09:00:00', worktimeEnd: '21:00:00', possibility: null, interior: [],
    },
  })
  @ApiNotFoundResponse({ type: ApiErrorResponseDto, description: 'Номенклатура отсутствует или не опубликована / Nomenclature is absent or not public.', example: { error: { code: 'NOMENCLATURE_NOT_FOUND', message: 'Nomenclature not found.' } } })
  findOne(@Param('identifier') identifier: string): Promise<NomenclatureDetailDto> {
    return this.publicCacheService.getOrSet('nomenclatures:detail', { identifier }, () => this.nomenclaturesService.findOne(identifier));
  }
}
