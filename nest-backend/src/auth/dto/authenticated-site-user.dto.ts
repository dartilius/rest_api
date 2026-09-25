import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class AuthenticatedSiteUserDto {
  @ApiProperty({ format: 'uuid', example: '00000000-0000-4000-8000-000000000001', description: 'UUID пользователя Django / Django user UUID.' })
  id!: string;

  @ApiPropertyOptional({ example: 'ordinary', description: 'Текущая роль из JWT Django / Current role from Django JWT.' })
  role?: string;

  @ApiProperty({ enum: ['rs256', 'legacy-hs256'], example: 'rs256', description: 'Алгоритм проверенного токена / Verified token algorithm.' })
  tokenVersion!: 'rs256' | 'legacy-hs256';
}
