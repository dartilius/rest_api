import 'reflect-metadata';
import './config/load-env';
import { BadRequestException, ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { ApiExceptionFilter } from './common/http/api-exception.filter';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  const origins = (process.env.CORS_ORIGINS ?? '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);

  if (origins.length) app.enableCors({ origin: origins });
  app.setGlobalPrefix('site-api/v1', { exclude: ['healthz'] });
  app.useGlobalPipes(new ValidationPipe({
    transform: true,
    whitelist: true,
    forbidNonWhitelisted: true,
    exceptionFactory: () => new BadRequestException({
      code: 'VALIDATION_ERROR',
      message: 'Request validation failed.',
    }),
  }));
  app.useGlobalFilters(new ApiExceptionFilter());

  const openApi = SwaggerModule.createDocument(app, new DocumentBuilder()
    .setTitle('RMC Site API')
    .setVersion('1.0')
    .setDescription([
      'API сайта RMC. Nest читает опубликованные данные Django/1С и не изменяет исходную БД.',
      '',
      'RMC website API. Nest reads published Django/1C data and never modifies the source database.',
      '',
      'Base path: `/site-api/v1`. Каталог публичный; `GET /auth/me` требует Django JWT в заголовке `Authorization: access_token <token>`.',
    ].join('\n'))
    .addApiKey({
      type: 'apiKey',
      in: 'header',
      name: 'Authorization',
      description: 'Вставьте `access_token <Django JWT>` целиком / Enter the full `access_token <Django JWT>` value.',
    }, 'django-access-token')
    .build());
  SwaggerModule.setup('site-api/docs', app, openApi);
  await app.listen(Number(process.env.PORT ?? 3001));
}

void bootstrap();
