import type { DataSourceOptions } from 'typeorm';

/**
 * Reserved for Nest-owned website tables and Django-produced read models.
 * No entity is registered yet, therefore it cannot create or alter a schema.
 */
export function websiteDataSourceOptions(env = process.env): Partial<DataSourceOptions> {
  return {
    type: 'postgres',
    schema: env.WEBSITE_DB_SCHEMA ?? 'website',
    synchronize: false,
    migrationsRun: false,
  };
}
