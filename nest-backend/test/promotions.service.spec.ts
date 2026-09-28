import assert from 'node:assert/strict';
import test from 'node:test';
import type { DataSource } from 'typeorm';
import { PromotionsService } from '../src/promotions/promotions.service';

test('maps a promotion without exposing source owner data', async () => {
  let call = 0;
  const source = { query: async () => {
    call += 1;
    return call === 1 ? [{ id: 'p', code1c: 'PROMO-1', name: 'Spring', description: null, is_active: true, start_period: '2026-03-01', end_period: null, created: '2026-02-01', counterparty: null }] : [{ total: '1' }];
  } } as unknown as DataSource;
  const service = new PromotionsService(source);

  const result = await service.list({ id: 'employee', role: 'manager', tokenVersion: 'rs256' }, { limit: 24, offset: 0 });

  assert.deepEqual(result.data[0], { id: 'p', code1c: 'PROMO-1', mainInfo: { name: 'Spring', description: null, relevance: true }, timeline: { start: '2026-03-01', end: null }, counterparty: null });
});
