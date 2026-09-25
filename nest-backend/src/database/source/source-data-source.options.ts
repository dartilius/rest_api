import { DataSource, type DataSourceOptions } from 'typeorm';
import '../../config/load-env';
import { sourceEntities } from './entities';

export const SOURCE_DATABASE_CONNECTION = 'source';

function required(name: string, env: NodeJS.ProcessEnv): string {
  const value = env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

export function sourceDataSourceOptions(env = process.env): DataSourceOptions {
  const port = Number(env.SOURCE_DB_PORT ?? '5432');
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('SOURCE_DB_PORT must be a valid TCP port');
  }

  return {
    name: SOURCE_DATABASE_CONNECTION,
    type: 'postgres',
    host: required('SOURCE_DB_HOST', env),
    port,
    database: required('SOURCE_DB_NAME', env),
    username: required('SOURCE_DB_USER', env),
    password: required('SOURCE_DB_PASSWORD', env),
    schema: env.SOURCE_DB_SCHEMA ?? 'public',
    entities: sourceEntities,
    synchronize: false,
    migrationsRun: false,
    logging: false,
    // Defence in depth. PostgreSQL role grants remain the authoritative control.
    extra: { options: '-c default_transaction_read_only=on' },
  };
}

export function createSourceDataSource(env = process.env): DataSource {
  return new DataSource(sourceDataSourceOptions(env));
}
