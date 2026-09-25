import { Controller, Get, Req, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiOperation, ApiUnauthorizedResponse, ApiTags } from '@nestjs/swagger';
import type { Request } from 'express';
import { ApiErrorResponseDto } from '../common/http/api-error.dto';
import { DjangoJwtAuthGuard } from './django-jwt-auth.guard';
import { AuthenticatedSiteUserDto } from './dto/authenticated-site-user.dto';
import type { AuthenticatedSiteUser } from './django-jwt-verifier.service';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  @Get('me')
  @UseGuards(DjangoJwtAuthGuard)
  @ApiBearerAuth('django-access-token')
  @ApiOperation({
    summary: 'Текущий пользователь / Current user',
    description: 'Требует access JWT, выпущенный Django. Заголовок: `Authorization: access_token <token>`. / Requires a Django-issued access JWT.',
  })
  @ApiOkResponse({
    type: AuthenticatedSiteUserDto,
    description: 'Проверенный пользователь и данные токена / Verified user and token metadata.',
  })
  @ApiUnauthorizedResponse({
    type: ApiErrorResponseDto,
    description: 'Токен отсутствует, просрочен или недействителен / Token is missing, expired, or invalid.',
    example: { error: { code: 'UNAUTHORIZED', message: 'Authentication required.' } },
  })
  me(@Req() request: Request & { user: AuthenticatedSiteUser }): AuthenticatedSiteUser {
    return request.user;
  }
}
