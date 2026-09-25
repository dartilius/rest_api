import { Transform, Type } from 'class-transformer';
import {
  ArrayMaxSize,
  IsArray,
  IsBoolean,
  IsIn,
  IsInt,
  IsOptional,
  IsString,
  IsUUID,
  Max,
  MaxLength,
  Matches,
  Min,
} from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

const CONTENT_TYPES = ['audio', 'video', 'audio_video', 'audio_video_image', 'video_image', 'audio_image'] as const;
const ORDERINGS = [
  'default', 'name', '-name', 'pricePerMonth', '-pricePerMonth',
  'version', '-version', 'timezone', '-timezone', 'brandName', '-brandName',
  'legalEntityName', '-legalEntityName', 'typeOfPlace', '-typeOfPlace', 'created', '-created',
] as const;

function stringArray(value: unknown): string[] | undefined {
  if (value === undefined || value === null || value === '') return undefined;
  const values = Array.isArray(value) ? value : String(value).split(',');
  return values.map(String).map((item) => item.trim()).filter(Boolean);
}

function trimmed(value: unknown): unknown {
  return typeof value === 'string' ? value.trim() : value;
}

export class NomenclatureFiltersDto {
  @ApiPropertyOptional({ maxLength: 100, example: 'экран', description: 'Код 1С, RASB id, полнотекстовый поиск или префикс названия / 1C code, RASB id, full-text search, or name prefix.' })
  @IsOptional() @IsString() @MaxLength(100) @Transform(({ value }) => trimmed(value))
  search?: string;

  @ApiPropertyOptional({ maxLength: 255, example: 'Медиаэкран', description: 'Подстрока названия / Name substring.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  name?: string;

  @ApiPropertyOptional({ format: 'uuid', example: '00000000-0000-4000-8000-000000000020' })
  @IsOptional() @IsUUID()
  id?: string;

  @ApiPropertyOptional({ maxLength: 64, example: '1C-DEMO-001', description: 'Точное значение кода 1С без учёта регистра / Case-insensitive exact 1C code.' })
  @IsOptional() @IsString() @MaxLength(64) @Transform(({ value }) => trimmed(value))
  code1c?: string;

  @ApiPropertyOptional({ type: [String], example: ['v2', 'v3'], description: 'Версии: JSON-массив в POST, повторяющийся или comma-separated параметр в GET / Versions: JSON array in POST, repeated or comma-separated parameter in GET.' })
  @IsOptional() @IsArray() @ArrayMaxSize(100) @IsString({ each: true }) @MaxLength(127, { each: true })
  @Transform(({ value }) => stringArray(value))
  versions?: string[];

  @ApiPropertyOptional({ maxLength: 127, example: 'v2', description: 'Подстрока версии / Version substring.' })
  @IsOptional() @IsString() @MaxLength(127) @Transform(({ value }) => trimmed(value))
  version?: string;

  @ApiPropertyOptional({ maxLength: 31, example: 'Asia/Krasnoyarsk' })
  @IsOptional() @IsString() @MaxLength(31) @Transform(({ value }) => trimmed(value))
  timezone?: string;

  @ApiPropertyOptional({ enum: ['0', '1', '2', '3', 'null'], example: '1', description: '`null` выбирает записи без статуса; `3` не применяет фильтр, как в Django / `null` selects records without a status; `3` disables the status filter.' })
  @IsOptional() @IsIn(['0', '1', '2', '3', 'null'])
  status?: '0' | '1' | '2' | '3' | 'null';

  @ApiPropertyOptional({ format: 'uuid', example: '00000000-0000-4000-8000-000000000010' })
  @IsOptional() @IsUUID()
  brandId?: string;

  @ApiPropertyOptional({ type: [String], example: ['00000000-0000-4000-8000-000000000010'], description: 'UUID брендов / Brand UUIDs.' })
  @IsOptional() @IsArray() @ArrayMaxSize(100) @IsUUID('4', { each: true })
  @Transform(({ value }) => stringArray(value))
  brandIds?: string[];

  @ApiPropertyOptional({ maxLength: 255, example: 'Demo Brand', description: 'Подстрока названия бренда / Brand name substring.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  brandName?: string;

  @ApiPropertyOptional({ type: [String], example: ['00000000-0000-4000-8000-000000000030'], description: 'UUID типов места / Type-of-place UUIDs.' })
  @IsOptional() @IsArray() @IsUUID('4', { each: true }) @Max(100)
  @Transform(({ value }) => stringArray(value))
  typeOfPlaceIds?: string[];

  @ApiPropertyOptional({ example: 'Торговый центр,Бизнес-центр', description: 'Точные имена типов места через запятую / Exact type-of-place names, comma-separated.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  typeOfPlace?: string;

  @ApiPropertyOptional({ maxLength: 255, example: 'krasnoyarsk', description: 'Slug города / City slug.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  citySlug?: string;

  @ApiPropertyOptional({ type: [String], example: ['krasnoyarsk', 'moscow'], description: 'Slug городов / City slugs.' })
  @IsOptional() @IsArray() @ArrayMaxSize(100) @IsString({ each: true }) @MaxLength(255, { each: true })
  @Transform(({ value }) => stringArray(value))
  citySlugs?: string[];

  @ApiPropertyOptional({ maxLength: 255, example: 'moscow', description: 'Исключаемый slug города / Excluded city slug.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  excludeCitySlug?: string;

  @ApiPropertyOptional({ maxLength: 255, example: 'ООО Демонстрация', description: 'Подстрока названия юрлица / Legal entity name substring.' })
  @IsOptional() @IsString() @MaxLength(255) @Transform(({ value }) => trimmed(value))
  legalEntityName?: string;

  @ApiPropertyOptional({ enum: CONTENT_TYPES, isArray: true, example: ['audio', 'video'], description: 'Типы контента / Content types.' })
  @IsOptional() @IsArray() @ArrayMaxSize(CONTENT_TYPES.length) @IsIn(CONTENT_TYPES, { each: true })
  @Transform(({ value }) => stringArray(value))
  contentTypes?: string[];

  @ApiPropertyOptional({ minimum: 0, example: '1000.00', description: 'Цена от, decimal-строка / Minimum price as a decimal string.' })
  @IsOptional() @IsString() @Matches(/^\d+(?:\.\d{1,2})?$/) @Transform(({ value }) => trimmed(value))
  priceFrom?: string;

  @ApiPropertyOptional({ minimum: 0, example: '5000.00', description: 'Цена до, decimal-строка / Maximum price as a decimal string.' })
  @IsOptional() @IsString() @Matches(/^\d+(?:\.\d{1,2})?$/) @Transform(({ value }) => trimmed(value))
  priceTo?: string;

  @ApiPropertyOptional({ example: true, description: 'Только с фасадным изображением или только без него / Only with or only without an exterior image.' })
  @IsOptional() @Transform(({ value }) => value === 'true' ? true : value === 'false' ? false : value) @IsBoolean()
  hasFacade?: boolean;

}

export class NomenclatureQueryDto extends NomenclatureFiltersDto {
  @ApiPropertyOptional({ enum: ORDERINGS, default: 'default', example: '-pricePerMonth', description: 'Порядок сортировки; минус означает убывание / Sort order; minus means descending.' })
  @IsOptional() @IsIn(ORDERINGS)
  ordering: typeof ORDERINGS[number] = 'default';

  @ApiPropertyOptional({ minimum: 1, default: 24, example: 24, description: 'Размер страницы без верхнего лимита на уровне API / Page size; API does not impose an upper limit.' })
  @IsOptional() @Type(() => Number) @IsInt() @Min(1)
  limit = 24;

  @ApiPropertyOptional({ minimum: 0, default: 0, example: 0, description: 'Смещение от начала списка / Offset from the first result.' })
  @IsOptional() @Type(() => Number) @IsInt() @Min(0)
  offset = 0;
}
