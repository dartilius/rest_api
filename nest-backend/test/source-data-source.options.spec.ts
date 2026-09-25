import assert from 'node:assert/strict';
import test from 'node:test';
import { sourceEntities } from '../src/database/source/entities';
import { sourceDataSourceOptions } from '../src/database/source/source-data-source.options';

test('source connection is read-only and cannot manage Django schema', () => {
  const options = sourceDataSourceOptions({
    SOURCE_DB_HOST: 'db', SOURCE_DB_PORT: '5432', SOURCE_DB_NAME: 'rmc',
    SOURCE_DB_USER: 'nest_source_reader', SOURCE_DB_PASSWORD: 'secret',
  });

  assert.equal(options.schema, 'public');
  assert.equal(options.synchronize, false);
  assert.equal(options.migrationsRun, false);
  assert.equal((options.extra as { options: string }).options, '-c default_transaction_read_only=on');
  assert.equal(sourceEntities.length, 37);
});
