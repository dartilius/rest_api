import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { SOURCE_DATABASE_CONNECTION } from '../database/source/source-data-source.options';
import { MinioReadService } from '../storage/minio-read.service';
import { NomenclatureFiltersDto, NomenclatureQueryDto } from './dto/nomenclature-query.dto';
import {
  NomenclatureBrandDto,
  NomenclatureDetailDto,
  NomenclatureFilterOptionsDto,
  NomenclatureImageDto,
  NomenclatureListItemDto,
  NomenclatureMapPointDto,
  NomenclatureMapResponseDto,
  NomenclatureTypeOfPlaceDto,
  NomenclaturesListResponseDto,
} from './dto/nomenclature-response.dto';

type NomenclatureRow = {
  id: string;
  description?: string | null;
  content_type?: string;
  worktime_start?: string | null;
  worktime_end?: string | null;
  possibility?: string | null;
  slots_per_hour: string | null;
  old_catalog_slug: string;
  price_per_month: string;
  brand_id: string | null;
  brand_name: string | null;
  brand_logotype: string | null;
  type_of_place_id: string | null;
  type_of_place_name: string | null;
  type_of_place_abbreviation: string | null;
  city_name: string | null;
  street_name: string | null;
  house_number: string | null;
  building_number: string | null;
  region_name?: string | null;
  region_type_name?: string | null;
  region_type_abbreviation?: string | null;
  region_type_show_before_name?: boolean | null;
  region_type_skip_in_name?: boolean | null;
  city_type_name?: string | null;
  city_type_abbreviation?: string | null;
  city_type_show_before_name?: boolean | null;
  administrative_unit_name?: string | null;
  microdistrict?: string | null;
  street_type_name?: string | null;
  street_type_abbreviation?: string | null;
  street_type_show_before_name?: boolean | null;
  latitude: string | null;
  longitude: string | null;
  exterior_id: string | null;
  exterior_source: string | null;
};

type ImageRow = { id: string; source: string; type: 'exterior' | 'interior' };
type MapRow = NomenclatureRow & { nomenclature_name: string; coordinates_id: string | null };
type FilterName = keyof NomenclatureFiltersDto;

const FILTER_FROM = `
  FROM public.nomenclature AS nomenclature
  LEFT JOIN public.brands AS brand ON brand.id = nomenclature.brand_id
  LEFT JOIN public.type_of_place AS type_of_place ON type_of_place.id = nomenclature."typeOfPlace_id"
  LEFT JOIN public.counterparties AS legal_entity ON legal_entity.id = nomenclature."legalEntity_id"
  LEFT JOIN public.nomenclature_addresses AS nomenclature_address
    ON nomenclature_address.nomenclature_id = nomenclature.id
  LEFT JOIN public.addresses_address AS address ON address.id = nomenclature_address.address_id
  LEFT JOIN public.addresses_city AS city ON city.id = address.city_id
  LEFT JOIN public.addresses_street AS street ON street.id = address.street_id
  LEFT JOIN public.addresses_house AS house ON house.id = address.house_id
  LEFT JOIN public.addresses_building AS building ON building.id = address.building_id
  LEFT JOIN public.addresses_coordinates AS coordinates ON coordinates.id = address.coordinates_id
  LEFT JOIN public.availability AS availability ON availability.client_id = nomenclature.id
`;

const CATALOG_FROM = `
  ${FILTER_FROM}
  LEFT JOIN LATERAL (
    SELECT image.id, image.source
    FROM public.nomenclature_images AS image
    WHERE image.nomenclature_id = nomenclature.id AND image.type = 'exterior'
    ORDER BY image.created DESC, image.id ASC
    LIMIT 1
  ) AS exterior ON TRUE
`;

const CATALOG_COLUMNS = `
  nomenclature.id::text AS id,
  nomenclature.description AS description,
  nomenclature."contentType" AS content_type,
  nomenclature.worktime_start::text AS worktime_start,
  nomenclature.worktime_end::text AS worktime_end,
  nomenclature.possibility AS possibility,
  nomenclature.slots_per_hour AS slots_per_hour,
  nomenclature.old_catalog_slug AS old_catalog_slug,
  nomenclature."pricePerMonth"::text AS price_per_month,
  brand.id::text AS brand_id,
  brand.name AS brand_name,
  brand.logotype AS brand_logotype,
  type_of_place.id::text AS type_of_place_id,
  type_of_place.name AS type_of_place_name,
  type_of_place.abbreviation AS type_of_place_abbreviation,
  city.name AS city_name,
  street.name AS street_name,
  house.number AS house_number,
  building.number AS building_number,
  coordinates.latitude AS latitude,
  coordinates.longitude AS longitude,
  exterior.id::text AS exterior_id,
  exterior.source AS exterior_source
`;

const MAP_COLUMNS = `
  ${CATALOG_COLUMNS},
  nomenclature.name AS nomenclature_name,
  coordinates.id::text AS coordinates_id
`;

const DETAIL_ADDRESS_FROM = `
  LEFT JOIN public.addresses_region AS region ON region.id = COALESCE(address.region_id, city.region_id)
  LEFT JOIN public.addresses_type_region AS region_type ON region_type.id = region.type_region_id
  LEFT JOIN public.addresses_locality_type AS city_type ON city_type.id = city.locality_type_id
  LEFT JOIN public.addresses_administrative_territorial_unit AS administrative_unit
    ON administrative_unit.id = address.administrative_unit_id
  LEFT JOIN public.addresses_street_type AS street_type ON street_type.id = street.street_type_id
`;

const DETAIL_ADDRESS_COLUMNS = `
  region.name AS region_name,
  region_type.name AS region_type_name,
  region_type.abbreviated_name AS region_type_abbreviation,
  region_type.show_before_name AS region_type_show_before_name,
  region_type.skip_in_name AS region_type_skip_in_name,
  city_type.name AS city_type_name,
  city_type.abbreviated_name AS city_type_abbreviation,
  city_type.show_before_name AS city_type_show_before_name,
  administrative_unit.name AS administrative_unit_name,
  address.microdistrict AS microdistrict,
  street_type.name AS street_type_name,
  street_type.abbreviated_name AS street_type_abbreviation,
  street_type.show_before_name AS street_type_show_before_name
`;

function escapedLike(value: string, mode: 'contains' | 'prefix' = 'contains'): string {
  const escaped = value.replaceAll('!', '!!').replaceAll('%', '!%').replaceAll('_', '!_');
  return mode === 'prefix' ? `${escaped}%` : `%${escaped}%`;
}

function splitNames(value: string | undefined): string[] | undefined {
  if (!value) return undefined;
  const result = value.split(',').map((item) => item.trim()).filter(Boolean);
  return result.length ? result : undefined;
}

function formatTypedName(
  name: string | null | undefined,
  typeName: string | null | undefined,
  typeAbbreviation: string | null | undefined,
  showBeforeName: boolean | null | undefined,
): string | null {
  if (!name) return null;
  if (!typeName) return name;
  const type = typeAbbreviation || typeName;
  return showBeforeName ? `${type} ${name}` : `${name} ${type}`;
}

function fullAddress(row: NomenclatureRow): string {
  const parts: string[] = [];
  if (row.region_name) {
    parts.push(row.region_type_skip_in_name
      ? row.region_name
      : (formatTypedName(
        row.region_name,
        row.region_type_name,
        row.region_type_abbreviation,
        row.region_type_show_before_name,
      ) ?? row.region_name));
  }

  const city = formatTypedName(
    row.city_name,
    row.city_type_name,
    row.city_type_abbreviation,
    row.city_type_show_before_name,
  );
  if (city) parts.push(city);

  if (row.administrative_unit_name?.trim()) {
    const district = row.administrative_unit_name.trim();
    parts.push(district.endsWith('р-н') || district.endsWith('район') ? district : `${district} р-н`);
  }
  if (row.microdistrict?.trim()) parts.push(`мкр. ${row.microdistrict.trim()}`);

  const street = formatTypedName(
    row.street_name,
    row.street_type_name,
    row.street_type_abbreviation,
    row.street_type_show_before_name,
  );
  if (street) parts.push(street);
  if (row.house_number) parts.push(`д. ${row.house_number}`);

  return parts.join(', ');
}

function mapPointName(row: MapRow): string {
  const title = [row.type_of_place_abbreviation, row.brand_name].filter(Boolean).join(' ');
  const address = [
    row.city_name && `г. ${row.city_name}`,
    row.street_name && `ул. ${row.street_name}`,
    row.house_number ?? row.building_number,
  ].filter((part): part is string => Boolean(part));
  return [title, ...address].filter(Boolean).join(', ') || row.nomenclature_name;
}

function perDay(row: MapRow): number | null {
  if (!row.slots_per_hour || !row.worktime_start || !row.worktime_end) return null;
  const minutes = (value: string): number | null => {
    const [hoursText, minutesText, secondsText = '0'] = value.split(':');
    const hours = Number(hoursText);
    const minutesPart = Number(minutesText);
    const seconds = Number(secondsText);
    if (![hours, minutesPart, seconds].every(Number.isFinite)) return null;
    return hours * 60 + minutesPart + seconds / 60;
  };
  const start = minutes(row.worktime_start);
  const end = minutes(row.worktime_end);
  const slotsPerHour = Number(row.slots_per_hour);
  if (start === null || end === null || !Number.isFinite(slotsPerHour)) return null;
  return slotsPerHour * ((end - start) / 60);
}

async function mapWithConcurrency<Input, Output>(
  values: Input[],
  concurrency: number,
  mapper: (value: Input) => Promise<Output>,
): Promise<Output[]> {
  const results = new Array<Output>(values.length);
  let nextIndex = 0;
  const worker = async (): Promise<void> => {
    while (nextIndex < values.length) {
      const index = nextIndex++;
      results[index] = await mapper(values[index]!);
    }
  };
  await Promise.all(Array.from({ length: Math.min(concurrency, values.length) }, worker));
  return results;
}

function sortClause(ordering: NomenclatureQueryDto['ordering']): string {
  const allowed: Record<NomenclatureQueryDto['ordering'], string> = {
    default: 'type_of_place.is_mall DESC NULLS LAST, tenant_count.count DESC, nomenclature.created DESC, nomenclature.id ASC',
    name: 'nomenclature.name ASC, nomenclature.id ASC',
    '-name': 'nomenclature.name DESC, nomenclature.id ASC',
    pricePerMonth: 'nomenclature."pricePerMonth" ASC, nomenclature.id ASC',
    '-pricePerMonth': 'nomenclature."pricePerMonth" DESC, nomenclature.id ASC',
    version: 'nomenclature.version ASC, nomenclature.id ASC',
    '-version': 'nomenclature.version DESC, nomenclature.id ASC',
    timezone: 'nomenclature.timezone ASC, nomenclature.id ASC',
    '-timezone': 'nomenclature.timezone DESC, nomenclature.id ASC',
    brandName: 'brand.name ASC NULLS LAST, nomenclature.id ASC',
    '-brandName': 'brand.name DESC NULLS LAST, nomenclature.id ASC',
    legalEntityName: 'legal_entity.keyword ASC NULLS LAST, nomenclature.id ASC',
    '-legalEntityName': 'legal_entity.keyword DESC NULLS LAST, nomenclature.id ASC',
    typeOfPlace: 'type_of_place.name ASC NULLS LAST, nomenclature.id ASC',
    '-typeOfPlace': 'type_of_place.name DESC NULLS LAST, nomenclature.id ASC',
    created: 'nomenclature.created ASC, nomenclature.id ASC',
    '-created': 'nomenclature.created DESC, nomenclature.id ASC',
  };
  return allowed[ordering];
}

@Injectable()
export class NomenclaturesService {
  constructor(
    @InjectDataSource(SOURCE_DATABASE_CONNECTION) private readonly sourceDataSource: DataSource,
    private readonly minioReadService: MinioReadService,
  ) {}

  async list(query: NomenclatureQueryDto): Promise<NomenclaturesListResponseDto> {
    const { where, params } = this.filters(query);
    const selectParams = [...params];
    const limitIndex = selectParams.push(query.limit);
    const offsetIndex = selectParams.push(query.offset);
    const rows = await this.sourceDataSource.query<NomenclatureRow[]>(`
      SELECT ${CATALOG_COLUMNS}
      ${CATALOG_FROM}
      LEFT JOIN LATERAL (
        SELECT COUNT(*)::integer AS count
        FROM public.nomenclature_tenant AS tenant
        WHERE tenant.nomenclature_id = nomenclature.id
      ) AS tenant_count ON TRUE
      ${where}
      ORDER BY ${sortClause(query.ordering)}
      LIMIT $${limitIndex} OFFSET $${offsetIndex}
    `, selectParams);
    const count = await this.sourceDataSource.query<Array<{ total: string }>>(`
      SELECT COUNT(*)::text AS total
      ${FILTER_FROM}
      ${where}
    `, params);

    return {
      data: await Promise.all(rows.map((row) => this.toListItem(row))),
      pagination: { total: Number(count[0]?.total ?? 0), limit: query.limit, offset: query.offset },
    };
  }

  async filterOptions(filters: NomenclatureFiltersDto): Promise<NomenclatureFilterOptionsDto> {
    const facet = async <Row>(
      select: string,
      excluded: readonly FilterName[],
      suffix: string,
    ): Promise<Row[]> => {
      const { where, params } = this.filters(filters, excluded);
      return this.sourceDataSource.query<Row[]>(`
        SELECT ${select}
        ${FILTER_FROM}
        ${where}
        ${suffix}
      `, params);
    };

    const [brands, typesOfPlace, cities, contentTypes, versions, timezones, statuses, facadeCounts, priceRows] = await Promise.all([
      facet<{ id: string; name: string; count: number }>(
        'brand.id::text AS id, brand.name AS name, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['brandId', 'brandIds', 'brandName'],
        'AND brand.id IS NOT NULL GROUP BY brand.id, brand.name ORDER BY brand.name ASC, brand.id ASC',
      ),
      facet<{ id: string; name: string; count: number }>(
        'type_of_place.id::text AS id, type_of_place.name AS name, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['typeOfPlaceIds', 'typeOfPlace'],
        'AND type_of_place.id IS NOT NULL GROUP BY type_of_place.id, type_of_place.name ORDER BY type_of_place.name ASC, type_of_place.id ASC',
      ),
      facet<{ slug: string; name: string; count: number }>(
        'city.slug AS slug, city.name AS name, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['citySlug', 'citySlugs'],
        'AND city.slug IS NOT NULL GROUP BY city.slug, city.name ORDER BY city.name ASC, city.slug ASC',
      ),
      facet<{ value: string; count: number }>(
        'nomenclature."contentType" AS value, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['contentTypes'],
        'AND nomenclature."contentType" IS NOT NULL GROUP BY nomenclature."contentType" ORDER BY nomenclature."contentType" ASC',
      ),
      facet<{ value: string; count: number }>(
        'nomenclature.version AS value, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['versions', 'version'],
        "AND nomenclature.version IS NOT NULL AND nomenclature.version <> '' GROUP BY nomenclature.version ORDER BY nomenclature.version ASC",
      ),
      facet<{ value: string; count: number }>(
        'nomenclature.timezone AS value, COUNT(DISTINCT nomenclature.id)::integer AS count',
        ['timezone'],
        'AND nomenclature.timezone IS NOT NULL GROUP BY nomenclature.timezone ORDER BY nomenclature.timezone ASC',
      ),
      facet<{ value: string; count: number }>(
        "COALESCE(availability.status::text, 'null') AS value, COUNT(DISTINCT nomenclature.id)::integer AS count",
        ['status'],
        "GROUP BY COALESCE(availability.status::text, 'null') ORDER BY COALESCE(availability.status::text, 'null') ASC",
      ),
      facet<{ with_facade: number; without_facade: number }>(
        `
          (COUNT(DISTINCT nomenclature.id) FILTER (WHERE EXISTS (
            SELECT 1 FROM public.nomenclature_images AS facade
            WHERE facade.nomenclature_id = nomenclature.id AND facade.type = 'exterior'
          )))::integer AS with_facade,
          (COUNT(DISTINCT nomenclature.id) FILTER (WHERE NOT EXISTS (
            SELECT 1 FROM public.nomenclature_images AS facade
            WHERE facade.nomenclature_id = nomenclature.id AND facade.type = 'exterior'
          )))::integer AS without_facade
        `,
        ['hasFacade'],
        '',
      ),
      facet<{ min: string | null; max: string | null }>(
        'MIN(nomenclature."pricePerMonth")::text AS min, MAX(nomenclature."pricePerMonth")::text AS max',
        ['priceFrom', 'priceTo'],
        '',
      ),
    ]);

    const facade = facadeCounts[0] ?? { with_facade: 0, without_facade: 0 };
    const price = priceRows[0] ?? { min: null, max: null };
    return {
      brands,
      typesOfPlace,
      cities,
      contentTypes,
      versions,
      timezones,
      statuses,
      hasFacade: [
        { value: true, count: facade.with_facade },
        { value: false, count: facade.without_facade },
      ],
      price,
    };
  }

  async map(filters: NomenclatureFiltersDto): Promise<NomenclatureMapResponseDto> {
    const { where, params } = this.filters(filters);
    const rows = await this.sourceDataSource.query<MapRow[]>(`
      SELECT ${MAP_COLUMNS}
      ${CATALOG_FROM}
      LEFT JOIN LATERAL (
        SELECT COUNT(*)::integer AS count
        FROM public.nomenclature_tenant AS tenant
        WHERE tenant.nomenclature_id = nomenclature.id
      ) AS tenant_count ON TRUE
      ${where}
      ORDER BY type_of_place.is_mall DESC NULLS LAST, tenant_count.count DESC, nomenclature.created DESC, nomenclature.id ASC
    `, params);

    return {
      count: rows.length,
      results: await mapWithConcurrency(rows, 20, (row) => this.toMapPoint(row)),
    };
  }

  async findOne(identifier: string): Promise<NomenclatureDetailDto> {
    const rows = await this.sourceDataSource.query<NomenclatureRow[]>(`
      SELECT ${CATALOG_COLUMNS}, ${DETAIL_ADDRESS_COLUMNS}
      ${CATALOG_FROM}
      ${DETAIL_ADDRESS_FROM}
      WHERE nomenclature.for_web = TRUE
        AND nomenclature.is_active = TRUE
        AND (
          nomenclature.id::text = $1
          OR nomenclature.code1c = $1
          OR nomenclature.old_catalog_slug = $1
        )
      ORDER BY CASE
        WHEN nomenclature.id::text = $1 THEN 0
        WHEN nomenclature.code1c = $1 THEN 1
        ELSE 2
      END ASC,
      CASE WHEN nomenclature.old_catalog_slug = $1 THEN nomenclature.created END DESC NULLS LAST,
      nomenclature.id ASC
      LIMIT 1
    `, [identifier]);
    const row = rows[0];
    if (!row) {
      throw new NotFoundException({ code: 'NOMENCLATURE_NOT_FOUND', message: 'Nomenclature not found.' });
    }
    const item = await this.toListItem(row);
    const images = await this.sourceDataSource.query<ImageRow[]>(`
      SELECT id::text AS id, source, type
      FROM public.nomenclature_images
      WHERE nomenclature_id = $1 AND type IN ('exterior', 'interior')
      ORDER BY type ASC, created DESC, id ASC
    `, [row.id]);
    const interior = await Promise.all(images.filter((image) => image.type === 'interior').map((image) => this.toImage(image)));

    return {
      ...item,
      address: { ...item.address, fullAddress: fullAddress(row) },
      description: row.description ?? null,
      contentType: row.content_type ?? '',
      worktimeStart: row.worktime_start ?? null,
      worktimeEnd: row.worktime_end ?? null,
      possibility: row.possibility ?? null,
      interior,
    };
  }

  private filters(
    query: NomenclatureFiltersDto,
    excluded: readonly FilterName[] = [],
  ): { where: string; params: unknown[] } {
    if (query.priceFrom !== undefined && query.priceTo !== undefined
      && Number(query.priceFrom) > Number(query.priceTo)) {
      throw new BadRequestException({ code: 'INVALID_PRICE_RANGE', message: 'priceFrom must not exceed priceTo.' });
    }
    const clauses = ['nomenclature.for_web = TRUE', 'nomenclature.is_active = TRUE'];
    const params: unknown[] = [];
    const enabled = (...names: FilterName[]): boolean => !names.some((name) => excluded.includes(name));
    const add = (clause: (index: number) => string, value: unknown): void => {
      params.push(value);
      clauses.push(clause(params.length));
    };
    const addLike = (column: string, value: string | undefined): void => {
      if (value) add((index) => `${column} ILIKE $${index} ESCAPE '!'`, escapedLike(value));
    };

    if (enabled('search') && query.search) {
      const exactIndex = params.push(query.search);
      const containsIndex = params.push(escapedLike(query.search));
      const prefixIndex = params.push(escapedLike(query.search, 'prefix'));
      clauses.push(`(nomenclature.code1c ILIKE $${exactIndex} ESCAPE '!'
        OR nomenclature.id_rasb ILIKE $${exactIndex} ESCAPE '!'
        OR nomenclature.search_vector ILIKE $${containsIndex} ESCAPE '!'
        OR nomenclature.name ILIKE $${prefixIndex} ESCAPE '!')`);
    }
    if (enabled('name')) addLike('nomenclature.name', query.name);
    if (enabled('id') && query.id) add((index) => `nomenclature.id = $${index}::uuid`, query.id);
    if (enabled('code1c') && query.code1c) add((index) => `nomenclature.code1c ILIKE $${index} ESCAPE '!'`, escapedLike(query.code1c));
    if (enabled('versions') && query.versions?.length) add((index) => `nomenclature.version = ANY($${index}::varchar[])`, query.versions);
    if (enabled('version')) addLike('nomenclature.version', query.version);
    if (enabled('timezone') && query.timezone) add((index) => `nomenclature.timezone ILIKE $${index} ESCAPE '!'`, escapedLike(query.timezone));
    if (enabled('status') && query.status === 'null') clauses.push('availability.status IS NULL');
    if (enabled('status') && query.status && query.status !== 'null' && query.status !== '3') add((index) => `availability.status = $${index}::smallint`, query.status);

    const brandIds = enabled('brandId', 'brandIds') ? [...(query.brandIds ?? []), ...(query.brandId ? [query.brandId] : [])] : [];
    if (brandIds.length) add((index) => `nomenclature.brand_id = ANY($${index}::uuid[])`, brandIds);
    if (enabled('brandName')) addLike('brand.name', query.brandName);
    if (enabled('typeOfPlaceIds') && query.typeOfPlaceIds?.length) add((index) => `nomenclature."typeOfPlace_id" = ANY($${index}::uuid[])`, query.typeOfPlaceIds);
    const typeNames = enabled('typeOfPlace') ? splitNames(query.typeOfPlace) : undefined;
    if (typeNames) add((index) => `type_of_place.name = ANY($${index}::varchar[])`, typeNames);

    const citySlugs = enabled('citySlug', 'citySlugs') ? [...(query.citySlugs ?? []), ...(query.citySlug ? [query.citySlug] : [])] : [];
    if (citySlugs.length) add((index) => `city.slug = ANY($${index}::varchar[])`, citySlugs);
    if (enabled('excludeCitySlug') && query.excludeCitySlug) add((index) => `city.slug <> $${index}`, query.excludeCitySlug);
    if (enabled('legalEntityName') && query.legalEntityName) {
      add((index) => `(legal_entity.keyword ILIKE $${index} ESCAPE '!'
        OR legal_entity.first_name ILIKE $${index} ESCAPE '!'
        OR legal_entity.middle_name ILIKE $${index} ESCAPE '!'
        OR legal_entity.last_name ILIKE $${index} ESCAPE '!'
        OR legal_entity.additional_name ILIKE $${index} ESCAPE '!'
        OR legal_entity.description ILIKE $${index} ESCAPE '!')`, escapedLike(query.legalEntityName));
    }
    if (enabled('contentTypes') && query.contentTypes?.length) add((index) => `nomenclature."contentType" = ANY($${index}::varchar[])`, query.contentTypes);
    if (enabled('priceFrom') && query.priceFrom !== undefined) add((index) => `nomenclature."pricePerMonth" >= $${index}::numeric`, query.priceFrom);
    if (enabled('priceTo') && query.priceTo !== undefined) add((index) => `nomenclature."pricePerMonth" <= $${index}::numeric`, query.priceTo);
    if (enabled('hasFacade') && query.hasFacade === true) clauses.push(`EXISTS (SELECT 1 FROM public.nomenclature_images AS facade WHERE facade.nomenclature_id = nomenclature.id AND facade.type = 'exterior')`);
    if (enabled('hasFacade') && query.hasFacade === false) clauses.push(`NOT EXISTS (SELECT 1 FROM public.nomenclature_images AS facade WHERE facade.nomenclature_id = nomenclature.id AND facade.type = 'exterior')`);

    return { where: `WHERE ${clauses.join('\n AND ')}`, params };
  }

  private async toListItem(row: NomenclatureRow): Promise<NomenclatureListItemDto> {
    const brand: NomenclatureBrandDto | null = row.brand_id && row.brand_name
      ? { id: row.brand_id, name: row.brand_name, logoUrl: await this.minioReadService.getReadUrl(row.brand_logotype) }
      : null;
    const exterior = row.exterior_id && row.exterior_source
      ? await this.toImage({ id: row.exterior_id, source: row.exterior_source, type: 'exterior' })
      : null;
    const typeOfPlace: NomenclatureTypeOfPlaceDto | null = row.type_of_place_id && row.type_of_place_name
      ? { id: row.type_of_place_id, name: row.type_of_place_name, abbreviation: row.type_of_place_abbreviation }
      : null;
    return {
      id: row.id,
      brand,
      exterior,
      address: {
        name: [row.city_name && `г. ${row.city_name}`, row.street_name && `ул. ${row.street_name}`, row.house_number ?? row.building_number]
          .filter((part): part is string => Boolean(part)).join(', '),
        coordinates: { latitude: row.latitude, longitude: row.longitude },
      },
      typeOfPlace,
      pricePerMonth: row.price_per_month,
      slotsPerHour: row.slots_per_hour,
      oldCatalogSlug: row.old_catalog_slug,
    };
  }

  private async toMapPoint(row: MapRow): Promise<NomenclatureMapPointDto> {
    const brand: NomenclatureBrandDto | null = row.brand_id && row.brand_name
      ? { id: row.brand_id, name: row.brand_name, logoUrl: await this.minioReadService.getReadUrl(row.brand_logotype) }
      : null;
    const facade = row.exterior_id && row.exterior_source
      ? await this.toImage({ id: row.exterior_id, source: row.exterior_source, type: 'exterior' })
      : null;
    const typeOfPlace: NomenclatureTypeOfPlaceDto | null = row.type_of_place_id && row.type_of_place_name
      ? { id: row.type_of_place_id, name: row.type_of_place_name, abbreviation: row.type_of_place_abbreviation }
      : null;
    return {
      id: row.id,
      name: mapPointName(row),
      coordinates: row.coordinates_id ? { latitude: row.latitude, longitude: row.longitude } : null,
      typeOfPlace,
      brand,
      facade,
      perDay: perDay(row),
      perHour: row.slots_per_hour,
      oldCatalogSlug: row.old_catalog_slug,
    };
  }

  private async toImage(image: ImageRow): Promise<NomenclatureImageDto> {
    return { id: image.id, url: await this.minioReadService.getReadUrl(image.source) };
  }
}
