import { ForbiddenException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service';
import { isContactPerson, isEmployee } from '../common/auth/site-access';
import { SOURCE_DATABASE_CONNECTION } from '../database/source/source-data-source.options';
import { PromotionQueryDto } from './dto/promotion-query.dto';

type Brand = { id: string; name: string; description: string | null };
type Counterparty = { id: string; name: string; brands: Brand[] } | null;
type Row = { id: string; code1c: string | null; name: string; description: string | null; is_active: boolean; start_period: string | null; end_period: string | null; created: string; counterparty: Counterparty };
export type PromotionListResponse = { data: Array<{ id: string; code1c: string | null; mainInfo: { name: string; description: string | null; relevance: boolean }; timeline: { start: string | null; end: string | null }; counterparty: Counterparty }>; pagination: { total: number; limit: number; offset: number } };
export type PromotionDetailResponse = { id: string; code1c: string | null; created: string; mainInfo: { name: string; description: string | null; relevance: boolean }; timeline: { start: string | null; end: string | null }; counterparty: Counterparty };

function pattern(value: string | undefined): string | null { return value?.trim() ? `%${value.trim().replaceAll('!', '!!').replaceAll('%', '!%').replaceAll('_', '!_')}%` : null; }
function toList(row: Row): PromotionListResponse['data'][number] { return { id: row.id, code1c: row.code1c, mainInfo: { name: row.name, description: row.description, relevance: row.is_active }, timeline: { start: row.start_period, end: row.end_period }, counterparty: row.counterparty }; }

@Injectable()
export class PromotionsService {
  constructor(@InjectDataSource(SOURCE_DATABASE_CONNECTION) private readonly source: DataSource) {}

  async list(user: AuthenticatedSiteUser, query: PromotionQueryDto): Promise<PromotionListResponse> {
    const { join, params } = this.scope(user);
    const search = pattern(query.search);
    const filters: string[] = [];
    if (search) { params.push(search); filters.push(`(promotion.name ILIKE $${params.length} ESCAPE '!' OR promotion.description ILIKE $${params.length} ESCAPE '!' OR promotion.code1c ILIKE $${params.length} ESCAPE '!')`); }
    const where = filters.length ? `WHERE ${filters.join(' AND ')}` : '';
    const limitIndex = params.push(query.limit); const offsetIndex = params.push(query.offset);
    const countParams = params.slice(0, -2);
    const [rows, count] = await Promise.all([
      this.source.query<Row[]>(`${this.select()} FROM public.promotions promotion ${join} ${where} ORDER BY promotion.created DESC, promotion.id DESC LIMIT $${limitIndex} OFFSET $${offsetIndex}`, params),
      this.source.query<Array<{ total: string }>>(`SELECT COUNT(DISTINCT promotion.id)::text AS total FROM public.promotions promotion ${join} ${where}`, countParams),
    ]);
    return { data: rows.map(toList), pagination: { total: Number(count[0]?.total ?? 0), limit: query.limit, offset: query.offset } };
  }

  async findOne(user: AuthenticatedSiteUser, identifier: string): Promise<PromotionDetailResponse> {
    const { join, params } = this.scope(user); params.push(identifier);
    const rows = await this.source.query<Row[]>(`${this.select()} FROM public.promotions promotion ${join} WHERE promotion.is_active = TRUE AND (promotion.id::text = $${params.length} OR promotion.code1c = $${params.length})`, params);
    const row = rows[0];
    if (!row) throw new NotFoundException({ code: 'PROMOTION_NOT_FOUND', message: 'Promotion not found.' });
    return { ...toList(row), created: row.created };
  }

  private select(): string {
    return `SELECT promotion.id::text AS id, promotion.code1c, promotion.name, promotion.description, promotion.is_active, promotion.start_period::text AS start_period, promotion.end_period::text AS end_period, promotion.created::text AS created,
      CASE WHEN counterparty.id IS NULL THEN NULL ELSE jsonb_build_object('id', counterparty.id::text, 'name', COALESCE(NULLIF(counterparty.keyword, ''), NULLIF(trim(concat_ws(' ', counterparty.first_name, counterparty.middle_name, counterparty.last_name)), ''), ''), 'brands', COALESCE((SELECT jsonb_agg(jsonb_build_object('id', brand.id::text, 'name', brand.name, 'description', brand.description) ORDER BY brand.name) FROM public.counterparties_brands assignment JOIN public.brands brand ON brand.id = assignment.brand_id WHERE assignment.counterparty_id = counterparty.id), '[]'::jsonb)) END AS counterparty`;
  }

  private scope(user: AuthenticatedSiteUser): { join: string; params: unknown[] } {
    if (isEmployee(user)) return { join: 'LEFT JOIN public.counterparties counterparty ON counterparty.id = promotion.counterparty_id', params: [] };
    if (isContactPerson(user)) return { join: 'INNER JOIN public.counterparties counterparty ON counterparty.id = promotion.counterparty_id INNER JOIN public.counterparties_contact_persons access_assignment ON access_assignment.counterparty_id = counterparty.id AND access_assignment.customuser_id = $1', params: [user.id] };
    throw new ForbiddenException({ code: 'PROMOTION_ACCESS_DENIED', message: 'Promotion access is not available for this role.' });
  }
}
