import { Module } from '@nestjs/common';
import { AuthController } from './auth.controller';
import { DjangoJwtAuthGuard } from './django-jwt-auth.guard';
import {
  DJANGO_JWT_CONFIG,
  DjangoJwtVerifier,
  djangoJwtConfigFromEnvironment,
} from './django-jwt-verifier.service';

@Module({
  controllers: [AuthController],
  providers: [
    { provide: DJANGO_JWT_CONFIG, useFactory: djangoJwtConfigFromEnvironment },
    DjangoJwtVerifier,
    DjangoJwtAuthGuard,
  ],
})
export class AuthModule {}
