import assert from 'node:assert/strict';
import test from 'node:test';
import { BadRequestException, NotFoundException } from '@nestjs/common';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import type { DataSource } from 'typeorm';
import { NomenclatureFiltersDto, NomenclatureQueryDto } from '../src/nomenclatures/dto/nomenclature-query.dto';
import { NomenclaturesService } from '../src/nomenclatures/nomenclatures.service';
import type { MinioReadService } from '../src/storage/minio-read.service';

const row = {
  id: '00000000-0000-0000-0000-000000000001',
  slots_per_hour: '2', old_catalog_slug: 'acme-krasnoyarsk', price_per_month: '1250.00',
  brand_id: '00000000-0000-0000-0000-000000000002', brand_name: 'Acme', brand_logotype: 'brand_logo/acme.png',
  type_of_place_id: '00000000-0000-0000-0000-000000000003', type_of_place_name: 'Mall', type_of_place_abbreviation: 'ТЦ',
  city_name: 'Красноярск', street_name: 'Мира', house_number: '5', building_number: null,
  region_name: 'Красноярский', region_type_name: 'край', region_type_abbreviation: 'кр.',
  region_type_show_before_name: false, region_type_skip_in_name: false,
  city_type_name: 'город', city_type_abbreviation: 'г.', city_type_show_before_name: true,
  administrative_unit_name: 'Советский', microdistrict: 'Взлетка',
  street_type_name: 'улица', street_type_abbreviation: 'ул.', street_type_show_before_name: true,
  latitude: '56.010', longitude: '92.870', exterior_id: '00000000-0000-0000-0000-000000000004', exterior_source: 'exterior/acme.jpg',
};

test('allows a nomenclature list limit above 100', async () => {
  const query = plainToInstance(NomenclatureQueryDto, { limit: '1000' });

  assert.deepEqual(await validate(query), []);
  assert.equal(query.limit, 1000);
});

test('lists public nomenclatures using parameterized filters and allow-listed output', async () => {
  const calls: Array<{ sql: string; params: unknown[] }> = [];
  const source = {
    query: async (sql: string, params: unknown[]) => {
      calls.push({ sql, params });
      return calls.length === 1 ? [row] : [{ total: '1' }];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async (key: string | null) => key ? `https://media.example/${key}` : null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.list({
    search: 'Acme%_', brandIds: ['00000000-0000-0000-0000-000000000002'],
    ordering: 'default', limit: 24, offset: 0,
  });

  assert.deepEqual(result, {
    data: [{
      id: row.id,
      brand: { id: row.brand_id, name: 'Acme', logoUrl: 'https://media.example/brand_logo/acme.png' },
      exterior: { id: row.exterior_id, url: 'https://media.example/exterior/acme.jpg' },
      address: { name: 'г. Красноярск, ул. Мира, 5', coordinates: { latitude: '56.010', longitude: '92.870' } },
      typeOfPlace: { id: row.type_of_place_id, name: 'Mall', abbreviation: 'ТЦ' },
      pricePerMonth: '1250.00', slotsPerHour: '2', oldCatalogSlug: 'acme-krasnoyarsk',
    }],
    pagination: { total: 1, limit: 24, offset: 0 },
  });
  assert.match(calls[0]?.sql ?? '', /nomenclature\.for_web = TRUE/);
  assert.match(calls[0]?.sql ?? '', /nomenclature\.is_active = TRUE/);
  assert.match(calls[0]?.sql ?? '', /nomenclature\.brand_id = ANY/);
  assert.deepEqual(calls[0]?.params.slice(0, 4), ['Acme%_', '%Acme!%!_%', 'Acme!%!_%', ['00000000-0000-0000-0000-000000000002']]);
});

test('returns contextual filter options without applying each facet own filter', async () => {
  const calls: Array<{ sql: string; params: unknown[] }> = [];
  const source = {
    query: async (sql: string, params: unknown[]) => {
      calls.push({ sql, params });
      if (sql.includes('brand.id::text')) return [{ id: row.brand_id, name: 'Acme', count: 2 }];
      if (sql.includes('type_of_place.id::text')) return [{ id: row.type_of_place_id, name: 'Mall', count: 2 }];
      if (sql.includes('city.slug AS slug')) return [{ slug: 'krasnoyarsk', name: 'Красноярск', count: 2 }];
      if (sql.includes('"contentType" AS value')) return [{ value: 'audio', count: 2 }];
      if (sql.includes('nomenclature.version AS value')) return [{ value: 'v2', count: 2 }];
      if (sql.includes('nomenclature.timezone AS value')) return [{ value: 'Asia/Krasnoyarsk', count: 2 }];
      if (sql.includes('COALESCE(availability.status')) return [{ value: '1', count: 2 }];
      if (sql.includes('with_facade')) return [{ with_facade: 2, without_facade: 1 }];
      return [{ min: '1000.00', max: '2500.00' }];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.filterOptions({
    brandId: row.brand_id,
    citySlug: 'krasnoyarsk',
    priceFrom: '1000.00',
  });

  assert.deepEqual(result, {
    brands: [{ id: row.brand_id, name: 'Acme', count: 2 }],
    typesOfPlace: [{ id: row.type_of_place_id, name: 'Mall', count: 2 }],
    cities: [{ slug: 'krasnoyarsk', name: 'Красноярск', count: 2 }],
    contentTypes: [{ value: 'audio', count: 2 }],
    versions: [{ value: 'v2', count: 2 }],
    timezones: [{ value: 'Asia/Krasnoyarsk', count: 2 }],
    statuses: [{ value: '1', count: 2 }],
    hasFacade: [{ value: true, count: 2 }, { value: false, count: 1 }],
    price: { min: '1000.00', max: '2500.00' },
  });
  const brandFacet = calls.find((call) => call.sql.includes('brand.id::text'));
  const cityFacet = calls.find((call) => call.sql.includes('city.slug AS slug'));
  assert.doesNotMatch(brandFacet?.sql ?? '', /nomenclature\.brand_id = ANY/);
  assert.match(cityFacet?.sql ?? '', /nomenclature\.brand_id = ANY/);
  assert.match(cityFacet?.sql ?? '', /COUNT\(DISTINCT nomenclature\.id\)/);
  assert.match(cityFacet?.sql ?? '', /nomenclature\.for_web = TRUE/);
});

test('validates filter-options body without pagination fields', async () => {
  const filters = plainToInstance(NomenclatureFiltersDto, {
    brandIds: ['00000000-0000-4000-8000-000000000002'],
    contentTypes: ['audio'],
  });

  assert.deepEqual(await validate(filters), []);
  assert.equal('limit' in filters, false);
  assert.equal('ordering' in filters, false);
});

test('returns all matching public map points with compact camelCase fields', async () => {
  const calls: Array<{ sql: string; params: unknown[] }> = [];
  const source = {
    query: async (sql: string, params: unknown[]) => {
      calls.push({ sql, params });
      return [{ ...row, nomenclature_name: 'Fallback name', coordinates_id: '00000000-0000-4000-8000-000000000010', worktime_start: '09:00:00', worktime_end: '21:00:00' }];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async (key: string | null) => key ? `signed:${key}` : null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.map({ citySlug: 'krasnoyarsk' });

  assert.deepEqual(result, {
    count: 1,
    results: [{
      id: row.id,
      name: 'ТЦ Acme, г. Красноярск, ул. Мира, 5',
      coordinates: { latitude: '56.010', longitude: '92.870' },
      typeOfPlace: { id: row.type_of_place_id, name: 'Mall', abbreviation: 'ТЦ' },
      brand: { id: row.brand_id, name: 'Acme', logoUrl: 'signed:brand_logo/acme.png' },
      facade: { id: row.exterior_id, url: 'signed:exterior/acme.jpg' },
      perDay: 24,
      perHour: '2',
      oldCatalogSlug: 'acme-krasnoyarsk',
    }],
  });
  assert.match(calls[0]?.sql ?? '', /nomenclature\.for_web = TRUE/);
  assert.match(calls[0]?.sql ?? '', /nomenclature\.is_active = TRUE/);
  assert.match(calls[0]?.sql ?? '', /ORDER BY type_of_place\.is_mall/);
  assert.doesNotMatch(calls[0]?.sql ?? '', /LIMIT\s+\$/);
  assert.deepEqual(calls[0]?.params, [['krasnoyarsk']]);
});

test('keeps a map point without coordinates and incomplete schedule', async () => {
  const source = {
    query: async () => [{
      ...row,
      nomenclature_name: 'Fallback name', coordinates_id: null, latitude: null, longitude: null,
      worktime_start: null, worktime_end: '21:00:00', type_of_place_abbreviation: null,
      brand_id: null, brand_name: null, exterior_id: null, exterior_source: null,
    }],
  } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.map({});

  assert.equal(result.results[0]?.coordinates, null);
  assert.equal(result.results[0]?.perDay, null);
  assert.equal(result.results[0]?.brand, null);
  assert.equal(result.results[0]?.facade, null);
  assert.equal(result.results[0]?.name, 'г. Красноярск, ул. Мира, 5');
});

test('returns public detail by legacy identifier and signs interior images only', async () => {
  const queries: string[] = [];
  const source = {
    query: async (sql: string, params: unknown[]) => {
      queries.push(sql);
      if (params[0] === 'legacy-slug') return [{ ...row, description: 'Public description', content_type: 'audio', worktime_start: '09:00:00', worktime_end: '22:00:00', possibility: 'high' }];
      return [
        { id: '00000000-0000-0000-0000-000000000005', source: 'interior/one.jpg', type: 'interior' },
        { id: '00000000-0000-0000-0000-000000000006', source: 'exterior/other.jpg', type: 'exterior' },
      ];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async (key: string | null) => key ? `signed:${key}` : null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.findOne('legacy-slug');

  assert.equal(result.description, 'Public description');
  assert.equal(result.contentType, 'audio');
  assert.equal(result.address.fullAddress, 'Красноярский кр., г. Красноярск, Советский р-н, мкр. Взлетка, ул. Мира, д. 5');
  assert.deepEqual(result.interior, [{ id: '00000000-0000-0000-0000-000000000005', url: 'signed:interior/one.jpg' }]);
  assert.match(queries[0] ?? '', /addresses_type_region AS region_type/);
  assert.match(queries[0] ?? '', /addresses_administrative_territorial_unit AS administrative_unit/);
});

test('formats a partial detail address with Django type and district rules', async () => {
  const source = {
    query: async (_sql: string, params: unknown[]) => {
      if (params[0] === 'partial') {
        return [{
          ...row,
          region_name: 'Москва', region_type_skip_in_name: true,
          city_name: 'Зеленоград', city_type_name: null,
          administrative_unit_name: 'Крюково р-н', microdistrict: '  ',
          street_name: 'Ленина', street_type_name: 'улица', street_type_abbreviation: null,
          street_type_show_before_name: false, house_number: null,
        }];
      }
      return [];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  const result = await service.findOne('partial');

  assert.equal(result.address.fullAddress, 'Москва, Зеленоград, Крюково р-н, Ленина улица');
});

test('rejects an inverted price range without querying the source database', async () => {
  const source = { query: async () => { throw new Error('must not query'); } } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  await assert.rejects(
    () => service.list({ priceFrom: '100.00', priceTo: '99.99', ordering: 'default', limit: 24, offset: 0 }),
    (error: unknown) => error instanceof BadRequestException,
  );
});

test('returns a stable not-found error for a non-public nomenclature', async () => {
  const source = { query: async () => [] } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new NomenclaturesService(source, minio);

  await assert.rejects(
    () => service.findOne('missing'),
    (error: unknown) => error instanceof NotFoundException
      && (error.getResponse() as { code: string }).code === 'NOMENCLATURE_NOT_FOUND',
  );
});
