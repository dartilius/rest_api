import { ApiProperty } from '@nestjs/swagger';

export class BrandListItemDto {
  @ApiProperty({ format: 'uuid', example: '00000000-0000-4000-8000-000000000010' })
  id!: string;
  @ApiProperty({ example: 'Demo Brand' })
  name!: string;
  @ApiProperty({ nullable: true, example: 'demo-brand' })
  slug!: string | null;
  @ApiProperty({ nullable: true, format: 'uri', example: 'https://media.example.local/local-media/brands/demo.png', description: 'Временная read-only ссылка MinIO или null / Temporary read-only MinIO URL or null.' })
  logoUrl!: string | null;
  @ApiProperty({ description: 'Цена хранится строкой, чтобы не потерять точность / Decimal string to preserve precision.', example: '1250.00' })
  minPrice!: string;
}

export class BrandDetailDto extends BrandListItemDto {
  @ApiProperty({ nullable: true, example: 'Демонстрационный бренд / Demo brand.' })
  description!: string | null;
}

export class BrandsListResponseDto {
  @ApiProperty({ type: BrandListItemDto, isArray: true })
  data!: BrandListItemDto[];
  @ApiProperty({ example: { total: 1, limit: 20, offset: 0 } })
  pagination!: { total: number; limit: number; offset: number };
}
