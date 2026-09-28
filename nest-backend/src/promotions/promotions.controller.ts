import { Controller, Get, Header, HttpCode, Param, Query, Req, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiNotFoundResponse, ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import type { Request } from 'express';
import { DjangoJwtAuthGuard } from '../auth/django-jwt-auth.guard';
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service';
import { PromotionQueryDto } from './dto/promotion-query.dto';
import { PromotionsService, type PromotionDetailResponse, type PromotionListResponse } from './promotions.service';

type SiteRequest = Request & { user: AuthenticatedSiteUser };

@ApiTags('Promotions') @ApiBearerAuth('django-access-token') @UseGuards(DjangoJwtAuthGuard) @Controller('promotions')
export class PromotionsController {
  constructor(private readonly promotions: PromotionsService) {}
  @Get() @HttpCode(200) @Header('Cache-Control', 'no-store') @ApiOperation({ summary: 'Акции, доступные текущему пользователю / List accessible promotions' }) @ApiOkResponse({ description: 'Paginated promotions.', example: { data: [{ id: '00000000-0000-4000-8000-000000000201', code1c: 'PROMO-1', mainInfo: { name: 'Весенняя акция', description: null, relevance: true }, timeline: { start: '2026-03-01', end: null }, counterparty: null }], pagination: { total: 1, limit: 24, offset: 0 } } })
  list(@Req() request: SiteRequest, @Query() query: PromotionQueryDto): Promise<PromotionListResponse> { return this.promotions.list(request.user, query); }
  @Get(':identifier') @HttpCode(200) @Header('Cache-Control', 'no-store') @ApiOperation({ summary: 'Акция по UUID или коду 1С / Get accessible promotion' }) @ApiNotFoundResponse({ description: 'Promotion is absent or inaccessible.' })
  findOne(@Req() request: SiteRequest, @Param('identifier') identifier: string): Promise<PromotionDetailResponse> { return this.promotions.findOne(request.user, identifier); }
}
