import { Module } from '@nestjs/common';
import { MinioReadService } from './minio-read.service';

@Module({ providers: [MinioReadService], exports: [MinioReadService] })
export class MinioReadModule {}
