import 'reflect-metadata';
import '../../config/load-env';
import { createSourceDataSource } from './source-data-source.options';

async function main(): Promise<void> {
  const dataSource = createSourceDataSource();
  try {
    await dataSource.initialize();
    const missing: string[] = [];

    for (const entity of dataSource.entityMetadatas) {
      const result = await dataSource.query(
        `SELECT column_name FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2`,
        [entity.schema ?? 'public', entity.tableName],
      ) as Array<{ column_name: string }>;
      const columns = new Set(result.map((row) => row.column_name));
      for (const column of entity.columns) {
        if (!columns.has(column.databaseName)) missing.push(`${entity.tablePath}.${column.databaseName}`);
      }
    }

    if (missing.length) throw new Error(`Source schema does not match mapped columns:\n${missing.join('\n')}`);
    console.log(`Verified ${dataSource.entityMetadatas.length} source entities.`);
  } finally {
    if (dataSource.isInitialized) await dataSource.destroy();
  }
}

void main();
