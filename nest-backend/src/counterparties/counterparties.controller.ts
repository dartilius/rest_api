import { Controller, Get, Header, HttpCode, Param, Query, Req, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiNotFoundResponse, ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import type { Request } from 'express';
import { DjangoJwtAuthGuard } from '../auth/django-jwt-auth.guard';
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service';
import { CounterpartyQueryDto } from './dto/counterparty-query.dto';
import { CounterpartiesService, type CounterpartyDetailResponse, type CounterpartyListResponse } from './counterparties.service';

type SiteRequest = Request & { user: AuthenticatedSiteUser };

@ApiTags('Counterparties')
@ApiBearerAuth('django-access-token')
@UseGuards(DjangoJwtAuthGuard)
@Controller('counterparties')
export class CounterpartiesController {
  constructor(private readonly counterparties: CounterpartiesService) {}

  @Get() @HttpCode(200) @Header('Cache-Control', 'no-store')
  @ApiOperation({ summary: 'Контрагенты, доступные текущему пользователю / List accessible counterparties' })
  @ApiOkResponse({ description: 'Paginated counterparties.', example: { data: [{ id: '00000000-0000-4000-8000-000000000101', name: 'ООО Ромашка, (Dealer, Brand A)', inn: '1234567890', brands: [{ id: '00000000-0000-4000-8000-000000000102', name: 'Brand A' }] }], pagination: { total: 1, limit: 24, offset: 0 } } })
  list(@Req() request: SiteRequest, @Query() query: CounterpartyQueryDto): Promise<CounterpartyListResponse> { return this.counterparties.list(request.user, query); }

  @Get(':identifier') @HttpCode(200) @Header('Cache-Control', 'no-store')
  @ApiOperation({ summary: 'Контрагент по UUID или коду 1С / Get accessible counterparty' })
  @ApiNotFoundResponse({ description: 'Counterparty is absent or inaccessible.' })
  findOne(@Req() request: SiteRequest, @Param('identifier') identifier: string): Promise<CounterpartyDetailResponse> { return this.counterparties.findOne(request.user, identifier); }
}
