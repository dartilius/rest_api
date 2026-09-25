import { ApiProperty } from '@nestjs/swagger';

export class ApiErrorDetailsDto {
  @ApiProperty({ example: 'VALIDATION_ERROR', description: 'Машинный код ошибки / Machine-readable error code.' })
  code!: string;

  @ApiProperty({ example: 'Request validation failed.', description: 'Человекочитаемое описание / Human-readable description.' })
  message!: string;
}

export class ApiErrorResponseDto {
  @ApiProperty({ type: ApiErrorDetailsDto })
  error!: ApiErrorDetailsDto;
}
