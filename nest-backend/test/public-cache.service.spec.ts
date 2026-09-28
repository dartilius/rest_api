import assert from 'node:assert/strict';
import test from 'node:test';
import { publicCacheKey, PublicCacheService } from '../src/common/cache/public-cache.service';

test('uses one cache key for equivalent public filter arrays and object field order', () => {
  const first = publicCacheKey('nomenclatures:list', {
    citySlugs: ['moscow', 'krasnoyarsk'],
    filters: { priceTo: '5000.00', priceFrom: '1000.00' },
  });
  const second = publicCacheKey('nomenclatures:list', {
    filters: { priceFrom: '1000.00', priceTo: '5000.00' },
    citySlugs: ['krasnoyarsk', 'moscow'],
  });

  assert.equal(first, second);
});

test('falls back to the source loader when Redis is disabled', async () => {
  const previousUrl = process.env.CACHE_REDIS_URL;
  delete process.env.CACHE_REDIS_URL;
  const cache = new PublicCacheService();
  let calls = 0;

  const result = await cache.getOrSet('brands:list', { limit: 20 }, async () => {
    calls += 1;
    return { data: ['Acme'] };
  });

  assert.deepEqual(result, { data: ['Acme'] });
  assert.equal(calls, 1);
  if (previousUrl === undefined) delete process.env.CACHE_REDIS_URL;
  else process.env.CACHE_REDIS_URL = previousUrl;
});

test('serves a Redis hit and does not call the source loader', async () => {
  const cache = new PublicCacheService();
  (cache as unknown as { client: unknown }).client = {
    isOpen: true,
    isReady: true,
    on: () => undefined,
    connect: async () => undefined,
    close: async () => undefined,
    get: async () => JSON.stringify({ data: ['cached'] }),
    set: async () => 'OK',
  };

  const result = await cache.getOrSet('brands:list', { limit: 20 }, async () => {
    throw new Error('source loader must not run for a cache hit');
  });

  assert.deepEqual(result, { data: ['cached'] });
});

test('continues with the source response when Redis reads or writes fail', async () => {
  const cache = new PublicCacheService();
  (cache as unknown as { client: unknown }).client = {
    isOpen: true,
    isReady: true,
    on: () => undefined,
    connect: async () => undefined,
    close: async () => undefined,
    get: async () => { throw new Error('Redis down'); },
    set: async () => { throw new Error('Redis down'); },
  };

  const result = await cache.getOrSet('brands:list', { limit: 20 }, async () => ({ data: ['source'] }));

  assert.deepEqual(result, { data: ['source'] });
});

test('coalesces concurrent cache misses for the same public request', async () => {
  const previousUrl = process.env.CACHE_REDIS_URL;
  delete process.env.CACHE_REDIS_URL;
  const cache = new PublicCacheService();
  let calls = 0;
  let release: (() => void) | undefined;
  const source = async () => {
    calls += 1;
    await new Promise<void>((resolve) => { release = resolve; });
    return { data: ['source'] };
  };

  const first = cache.getOrSet('brands:list', { limit: 20 }, source);
  const second = cache.getOrSet('brands:list', { limit: 20 }, source);
  await new Promise((resolve) => setImmediate(resolve));
  release?.();

  assert.deepEqual(await Promise.all([first, second]), [{ data: ['source'] }, { data: ['source'] }]);
  assert.equal(calls, 1);
  if (previousUrl === undefined) delete process.env.CACHE_REDIS_URL;
  else process.env.CACHE_REDIS_URL = previousUrl;
});
