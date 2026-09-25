import { Module } from '@nestjs/common';
import { SourceDatabaseModule } from '../database/source/source-database.module';
import { MinioReadModule } from '../storage/minio-read.module';
import { NomenclaturesController } from './nomenclatures.controller';
import { NomenclaturesService } from './nomenclatures.service';

@Module({
  imports: [SourceDatabaseModule, MinioReadModule],
  controllers: [NomenclaturesController],
  providers: [NomenclaturesService],
})
export class NomenclaturesModule {}
