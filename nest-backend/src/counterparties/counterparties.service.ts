import { ForbiddenException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service';
import { isContactPerson, isEmployee } from '../common/auth/site-access';
import { SOURCE_DATABASE_CONNECTION } from '../database/source/source-data-source.options';
import { CounterpartyQueryDto } from './dto/counterparty-query.dto';

type Brand = { id: string; name: string };
type ContactPerson = { id: string; firstName: string | null; lastName: string | null; middleName: string | null; email: string | null };
type Contact = { id: string; basic: boolean; type: string | null; meaning: string | null; ext: string | null; comment: string | null };
type Row = { id: string; code1c: string | null; opf: string | null; inn: string | null; first_name: string; middle_name: string; last_name: string; description: string | null; keyword: string | null; additional_name: string | null; broadcast: boolean; is_active: boolean; created: string; brands: Brand[]; contact_persons?: ContactPerson[]; contacts?: Contact[] };

export type CounterpartyListResponse = { data: Array<{ id: string; name: string; inn: string | null; brands: Brand[] }>; pagination: { total: number; limit: number; offset: number } };
export type CounterpartyDetailResponse = { id: string; code1c: string | null; opf: string | null; inn: string | null; firstName: string; middleName: string; lastName: string; name: string; description: string | null; keyword: string | null; additionalName: string | null; broadcast: boolean; isActive: boolean; created: string; brands: Brand[]; contactPersons: ContactPerson[]; contacts: Contact[] };

function nameOf(row: Row): string {
  const brandNames = row.brands.map((brand) => brand.name).join(', ');
  const details = [row.description, brandNames].filter(Boolean).join(', ');
  const fio = [row.first_name, row.middle_name, row.last_name].filter(Boolean).join(' ');
  if (!row.opf) return row.keyword || details;
  if (['IP', 'FL', 'SE'].includes(row.opf)) return details ? `${fio}, (${details})` : fio;
  return details ? `${row.keyword || fio}, (${details})` : (row.keyword || fio);
}

function searchPattern(value: string | undefined): string | null {
  if (!value?.trim()) return null;
  return `%${value.trim().replaceAll('!', '!!').replaceAll('%', '!%').replaceAll('_', '!_')}%`;
}

@Injectable()
export class CounterpartiesService {
  constructor(@InjectDataSource(SOURCE_DATABASE_CONNECTION) private readonly source: DataSource) {}

  async list(user: AuthenticatedSiteUser, query: CounterpartyQueryDto): Promise<CounterpartyListResponse> {
    const { join, params } = this.scope(user);
    const pattern = searchPattern(query.search);
    const filters = ['counterparty.is_active = TRUE'];
    if (pattern) { params.push(pattern); filters.push(`(counterparty.keyword ILIKE $${params.length} ESCAPE '!' OR counterparty.first_name ILIKE $${params.length} ESCAPE '!' OR counterparty.middle_name ILIKE $${params.length} ESCAPE '!' OR counterparty.last_name ILIKE $${params.length} ESCAPE '!' OR counterparty.inn ILIKE $${params.length} ESCAPE '!' OR counterparty.code1c ILIKE $${params.length} ESCAPE '!')`); }
    const where = `WHERE ${filters.join(' AND ')}`;
    const limitIndex = params.push(query.limit);
    const offsetIndex = params.push(query.offset);
    const countParams = params.slice(0, -(2));
    const [rows, count] = await Promise.all([
      this.source.query<Row[]>(`
        SELECT counterparty.id::text AS id, counterparty.code1c, counterparty.opf, counterparty.inn, counterparty.first_name, counterparty.middle_name, counterparty.last_name, counterparty.description, counterparty.keyword, counterparty.additional_name, counterparty.broadcast, counterparty.is_active, counterparty.created::text AS created,
          COALESCE((SELECT jsonb_agg(jsonb_build_object('id', brand.id::text, 'name', brand.name) ORDER BY brand.name) FROM public.counterparties_brands counterparty_brand JOIN public.brands brand ON brand.id = counterparty_brand.brand_id WHERE counterparty_brand.counterparty_id = counterparty.id), '[]'::jsonb) AS brands
        FROM public.counterparties counterparty ${join} ${where}
        ORDER BY counterparty.created DESC, counterparty.id DESC LIMIT $${limitIndex} OFFSET $${offsetIndex}
      `, params),
      this.source.query<Array<{ total: string }>>(`SELECT COUNT(DISTINCT counterparty.id)::text AS total FROM public.counterparties counterparty ${join} ${where}`, countParams),
    ]);
    return { data: rows.map((row) => ({ id: row.id, name: nameOf(row), inn: row.inn, brands: row.brands })), pagination: { total: Number(count[0]?.total ?? 0), limit: query.limit, offset: query.offset } };
  }

  async findOne(user: AuthenticatedSiteUser, identifier: string): Promise<CounterpartyDetailResponse> {
    const { join, params } = this.scope(user);
    params.push(identifier);
    const rows = await this.source.query<Row[]>(`
      SELECT counterparty.id::text AS id, counterparty.code1c, counterparty.opf, counterparty.inn, counterparty.first_name, counterparty.middle_name, counterparty.last_name, counterparty.description, counterparty.keyword, counterparty.additional_name, counterparty.broadcast, counterparty.is_active, counterparty.created::text AS created,
        COALESCE((SELECT jsonb_agg(jsonb_build_object('id', brand.id::text, 'name', brand.name) ORDER BY brand.name) FROM public.counterparties_brands counterparty_brand JOIN public.brands brand ON brand.id = counterparty_brand.brand_id WHERE counterparty_brand.counterparty_id = counterparty.id), '[]'::jsonb) AS brands,
        COALESCE((SELECT jsonb_agg(jsonb_build_object('id', person.id::text, 'firstName', person.first_name, 'lastName', person.last_name, 'middleName', person.middle_name, 'email', person.email) ORDER BY person.last_name, person.first_name) FROM public.counterparties_contact_persons assignment JOIN public.custom_user person ON person.id = assignment.customuser_id WHERE assignment.counterparty_id = counterparty.id), '[]'::jsonb) AS contact_persons,
        COALESCE((SELECT jsonb_agg(jsonb_build_object('id', contact.id::text, 'basic', contact.basic, 'type', contact.type, 'meaning', contact.meaning, 'ext', contact.ext, 'comment', contact.comment) ORDER BY contact.basic DESC, contact.id) FROM public.counterparty_contact_info contact WHERE contact.counterparty_id = counterparty.id), '[]'::jsonb) AS contacts
      FROM public.counterparties counterparty ${join}
      WHERE counterparty.is_active = TRUE AND (counterparty.id::text = $${params.length} OR counterparty.code1c = $${params.length})
    `, params);
    const row = rows[0];
    if (!row) throw new NotFoundException({ code: 'COUNTERPARTY_NOT_FOUND', message: 'Counterparty not found.' });
    return { id: row.id, code1c: row.code1c, opf: row.opf, inn: row.inn, firstName: row.first_name, middleName: row.middle_name, lastName: row.last_name, name: nameOf(row), description: row.description, keyword: row.keyword, additionalName: row.additional_name, broadcast: row.broadcast, isActive: row.is_active, created: row.created, brands: row.brands, contactPersons: row.contact_persons ?? [], contacts: row.contacts ?? [] };
  }

  private scope(user: AuthenticatedSiteUser): { join: string; params: unknown[] } {
    if (isEmployee(user)) return { join: '', params: [] };
    if (isContactPerson(user)) return { join: 'INNER JOIN public.counterparties_contact_persons access_assignment ON access_assignment.counterparty_id = counterparty.id AND access_assignment.customuser_id = $1', params: [user.id] };
    throw new ForbiddenException({ code: 'COUNTERPARTY_ACCESS_DENIED', message: 'Counterparty access is not available for this role.' });
  }
}
