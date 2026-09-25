import { Module } from '@nestjs/common';
import { AuthModule } from './auth/auth.module';
import { BrandsModule } from './brands/brands.module';
import { SourceDatabaseModule } from './database/source/source-database.module';
import { WebsiteDatabaseModule } from './database/website/website-database.module';
import { HealthModule } from './health/health.module';
import { NomenclaturesModule } from './nomenclatures/nomenclatures.module';

@Module({ imports: [SourceDatabaseModule, WebsiteDatabaseModule, HealthModule, AuthModule, BrandsModule, NomenclaturesModule] })
export class AppModule {}
