import { Transform, Type } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, MaxLength, Min } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class BrandQueryDto {
  @ApiPropertyOptional({ maxLength: 100, example: 'demo', description: 'Поиск без учёта регистра по названию, slug или коду 1С / Case-insensitive search by name, slug, or 1C code.' })
  @IsOptional()
  @IsString()
  @MaxLength(100)
  @Transform(({ value }) => typeof value === 'string' ? value.trim() : value)
  search?: string;

  @ApiPropertyOptional({ minimum: 1, maximum: 100, default: 20, example: 20, description: 'Размер страницы / Page size.' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit = 20;

  @ApiPropertyOptional({ minimum: 0, default: 0, example: 0, description: 'Смещение от начала / Offset from the first item.' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  offset = 0;
}
