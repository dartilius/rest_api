import assert from 'node:assert/strict';
import test from 'node:test';
import { NotFoundException } from '@nestjs/common';
import type { DataSource } from 'typeorm';
import { BrandsService } from '../src/brands/brands.service';
import type { MinioReadService } from '../src/storage/minio-read.service';

test('lists public brands with bounded search parameters and allow-listed output', async () => {
  const calls: Array<{ sql: string; params: unknown[] }> = [];
  const sourceDataSource = {
    query: async (sql: string, params: unknown[]) => {
      calls.push({ sql, params });
      if (calls.length === 1) {
        return [{
          id: '00000000-0000-0000-0000-000000000001', name: 'Acme', slug: 'acme',
          logotype: 'brand_logo/acme.png', min_price: '1250.00', is_deleted: false,
        }];
      }
      return [{ total: '1' }];
    },
  } as unknown as DataSource;
  const minio = { getReadUrl: async () => 'https://media.example/acme' } as unknown as MinioReadService;
  const service = new BrandsService(sourceDataSource, minio);

  const result = await service.list({ search: 'Acme%_!', limit: 20, offset: 0 });

  assert.deepEqual(result, {
    data: [{
      id: '00000000-0000-0000-0000-000000000001', name: 'Acme', slug: 'acme',
      logoUrl: 'https://media.example/acme', minPrice: '1250.00',
    }],
    pagination: { total: 1, limit: 20, offset: 0 },
  });
  assert.deepEqual(calls[0]?.params, ['%Acme!%!_!!%', 20, 0]);
  assert.match(calls[0]?.sql ?? '', /brand\.is_deleted = FALSE/);
  assert.match(calls[0]?.sql ?? '', /nomenclature\.for_web = TRUE/);
});

test('returns a stable not-found error for a non-public brand', async () => {
  const sourceDataSource = { query: async () => [] } as unknown as DataSource;
  const minio = { getReadUrl: async () => null } as unknown as MinioReadService;
  const service = new BrandsService(sourceDataSource, minio);

  await assert.rejects(
    () => service.findOne('missing'),
    (error: unknown) => error instanceof NotFoundException
      && (error.getResponse() as { code: string }).code === 'BRAND_NOT_FOUND',
  );
});
