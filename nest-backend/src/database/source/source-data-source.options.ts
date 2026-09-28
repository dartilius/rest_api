import { DataSource, type DataSourceOptions } from 'typeorm';
import '../../config/load-env';
import { sourceEntities } from './entities';

export const SOURCE_DATABASE_CONNECTION = 'source';

function required(name: string, env: NodeJS.ProcessEnv): string {
  const value = env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

function positiveInteger(name: string, value: string | undefined, fallback: number): number {
  const parsed = Number(value ?? fallback);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${name} must be a positive integer`);
  }
  return parsed;
}

export function sourceDataSourceOptions(env = process.env): DataSourceOptions {
  const port = Number(env.SOURCE_DB_PORT ?? '5432');
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('SOURCE_DB_PORT must be a valid TCP port');
  }
  const poolMax = positiveInteger('SOURCE_DB_POOL_MAX', env.SOURCE_DB_POOL_MAX, 10);
  const connectionTimeoutMillis = positiveInteger(
    'SOURCE_DB_CONNECTION_TIMEOUT_MS',
    env.SOURCE_DB_CONNECTION_TIMEOUT_MS,
    3_000,
  );
  const queryTimeout = positiveInteger('SOURCE_DB_QUERY_TIMEOUT_MS', env.SOURCE_DB_QUERY_TIMEOUT_MS, 5_000);
  const statementTimeout = positiveInteger(
    'SOURCE_DB_STATEMENT_TIMEOUT_MS',
    env.SOURCE_DB_STATEMENT_TIMEOUT_MS,
    5_000,
  );

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
    // PostgreSQL grants remain authoritative. The remaining limits prevent one
    // slow catalogue query from holding every reader connection indefinitely.
    extra: {
      options: `-c default_transaction_read_only=on -c statement_timeout=${statementTimeout}`,
      max: poolMax,
      connectionTimeoutMillis,
      query_timeout: queryTimeout,
      statement_timeout: statementTimeout,
    },
  };
}

export function createSourceDataSource(env = process.env): DataSource {
  return new DataSource(sourceDataSourceOptions(env));
}
