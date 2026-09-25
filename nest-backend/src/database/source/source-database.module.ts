import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { sourceDataSourceOptions, SOURCE_DATABASE_CONNECTION } from './source-data-source.options';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      name: SOURCE_DATABASE_CONNECTION,
      useFactory: () => sourceDataSourceOptions(),
    }),
  ],
  exports: [TypeOrmModule],
})
export class SourceDatabaseModule {}
