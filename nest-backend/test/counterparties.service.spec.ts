import assert from 'node:assert/strict';
import test from 'node:test';
import { ForbiddenException } from '@nestjs/common';
import type { DataSource } from 'typeorm';
import { CounterpartiesService } from '../src/counterparties/counterparties.service';

test('lists only active counterparties and returns a computed display name', async () => {
  let call = 0;
  const source = { query: async () => {
    call += 1;
    return call === 1 ? [{ id: 'a', code1c: 'CP-1', opf: 'OOO', inn: '123', first_name: '', middle_name: '', last_name: '', description: 'Dealer', keyword: 'Acme', additional_name: null, broadcast: false, is_active: true, created: '2026-01-01', brands: [{ id: 'b', name: 'Brand' }] }] : [{ total: '1' }];
  } } as unknown as DataSource;
  const service = new CounterpartiesService(source);

  const result = await service.list({ id: 'user', role: 'manager', tokenVersion: 'rs256' }, { limit: 24, offset: 0 });

  assert.deepEqual(result.data, [{ id: 'a', name: 'Acme, (Dealer, Brand)', inn: '123', brands: [{ id: 'b', name: 'Brand' }] }]);
});

test('rejects counterparty access for a role without Django access', async () => {
  const service = new CounterpartiesService({ query: async () => [] } as unknown as DataSource);
  await assert.rejects(() => service.list({ id: 'user', role: 'ordinary', tokenVersion: 'rs256' }, { limit: 24, offset: 0 }), ForbiddenException);
});
