import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';

@ApiTags('Health')
@Controller('healthz')
export class HealthController {
  @Get()
  @ApiOperation({ summary: 'Проверка работоспособности / Liveness check', description: 'Внутренний endpoint для Kubernetes. Не имеет префикса `/site-api/v1`. / Internal endpoint for Kubernetes without the API prefix.' })
  @ApiOkResponse({ schema: { example: { status: 'ok' } } })
  getHealth(): { status: 'ok' } {
    return { status: 'ok' };
  }
}
