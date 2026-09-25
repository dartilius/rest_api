import { Module } from '@nestjs/common';
import { SourceDatabaseModule } from '../database/source/source-database.module';
import { MinioReadModule } from '../storage/minio-read.module';
import { BrandsController } from './brands.controller';
import { BrandsService } from './brands.service';

@Module({
  imports: [SourceDatabaseModule, MinioReadModule],
  controllers: [BrandsController],
  providers: [BrandsService],
})
export class BrandsModule {}
