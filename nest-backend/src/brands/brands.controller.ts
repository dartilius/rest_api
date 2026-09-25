import { Controller, Get, Header, HttpCode, Param, Query } from '@nestjs/common';
import { ApiNotFoundResponse, ApiOkResponse, ApiOperation, ApiParam, ApiTags } from '@nestjs/swagger';
import { ApiErrorResponseDto } from '../common/http/api-error.dto';
import { BrandQueryDto } from './dto/brand-query.dto';
import { BrandDetailDto, BrandsListResponseDto } from './dto/brand-response.dto';
import { BrandsService } from './brands.service';

@ApiTags('Brands')
@Controller('brands')
export class BrandsController {
  constructor(private readonly brandsService: BrandsService) {}

  @Get()
  @HttpCode(200)
  @Header('Cache-Control', 'no-store')
  @ApiOperation({
    summary: 'Список публичных брендов / List public brands',
    description: 'Возвращает только неудалённые бренды с хотя бы одной активной опубликованной номенклатурой. / Returns only non-deleted brands with active published nomenclatures.',
  })
  @ApiOkResponse({
    type: BrandsListResponseDto,
    example: {
      data: [{ id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', slug: 'demo-brand', logoUrl: 'https://media.example.local/local-media/brands/demo.png', minPrice: '1250.00' }],
      pagination: { total: 1, limit: 20, offset: 0 },
    },
  })
  list(@Query() query: BrandQueryDto): Promise<BrandsListResponseDto> {
    return this.brandsService.list(query);
  }

  @Get(':identifier')
  @HttpCode(200)
  @Header('Cache-Control', 'no-store')
  @ApiOperation({ summary: 'Публичный бренд по идентификатору / Get a public brand by identifier' })
  @ApiParam({ name: 'identifier', description: 'UUID, slug или код 1С / UUID, slug, or 1C code.', example: 'demo-brand' })
  @ApiOkResponse({
    type: BrandDetailDto,
    example: { id: '00000000-0000-4000-8000-000000000010', name: 'Demo Brand', slug: 'demo-brand', logoUrl: null, minPrice: '1250.00', description: 'Демонстрационный бренд / Demo brand.' },
  })
  @ApiNotFoundResponse({ type: ApiErrorResponseDto, description: 'Бренд отсутствует, удалён или не имеет публичных номенклатур / Brand is absent, deleted, or has no public nomenclatures.', example: { error: { code: 'BRAND_NOT_FOUND', message: 'Brand not found.' } } })
  findOne(@Param('identifier') identifier: string): Promise<BrandDetailDto> {
    return this.brandsService.findOne(identifier);
  }
}
