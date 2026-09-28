import { Module } from '@nestjs/common';
import { AuthModule } from './auth/auth.module';
import { BrandsModule } from './brands/brands.module';
import { SourceDatabaseModule } from './database/source/source-database.module';
import { WebsiteDatabaseModule } from './database/website/website-database.module';
import { HealthModule } from './health/health.module';
import { NomenclaturesModule } from './nomenclatures/nomenclatures.module';
import { CounterpartiesModule } from './counterparties/counterparties.module';
import { PromotionsModule } from './promotions/promotions.module';
import { UsersModule } from './users/users.module';
import { PublicCacheModule } from './common/cache/public-cache.module';

@Module({ imports: [PublicCacheModule, SourceDatabaseModule, WebsiteDatabaseModule, HealthModule, AuthModule, BrandsModule, NomenclaturesModule, CounterpartiesModule, PromotionsModule, UsersModule] })
export class AppModule {}
