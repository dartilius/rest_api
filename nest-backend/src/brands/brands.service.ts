import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { SOURCE_DATABASE_CONNECTION } from '../database/source/source-data-source.options';
import { MinioReadService } from '../storage/minio-read.service';
import { BrandDetailDto, BrandListItemDto, BrandsListResponseDto } from './dto/brand-response.dto';
import { BrandQueryDto } from './dto/brand-query.dto';

type BrandRow = {
  id: string;
  name: string;
  slug: string | null;
  description?: string | null;
  logotype: string | null;
  min_price: string;
};

const VISIBLE_BRANDS_FROM = `
  FROM public.brands AS brand
  INNER JOIN public.nomenclature AS nomenclature
    ON nomenclature.brand_id = brand.id
    AND nomenclature.for_web = TRUE
    AND nomenclature.is_active = TRUE
  WHERE brand.is_deleted = FALSE
`;

function searchPattern(search: string | undefined): string | null {
  if (!search) return null;
  return `%${search.replaceAll('!', '!!').replaceAll('%', '!%').replaceAll('_', '!_')}%`;
}

@Injectable()
export class BrandsService {
  constructor(
    @InjectDataSource(SOURCE_DATABASE_CONNECTION) private readonly sourceDataSource: DataSource,
    private readonly minioReadService: MinioReadService,
  ) {}

  async list(query: BrandQueryDto): Promise<BrandsListResponseDto> {
    const pattern = searchPattern(query.search);
    const filter = pattern
      ? `AND (brand.name ILIKE $1 ESCAPE '!' OR brand.slug ILIKE $1 ESCAPE '!' OR brand.code1c ILIKE $1 ESCAPE '!')`
      : '';
    const queryParams: unknown[] = pattern ? [pattern] : [];
    const limitIndex = queryParams.push(query.limit);
    const offsetIndex = queryParams.push(query.offset);

    const rows = await this.sourceDataSource.query<BrandRow[]>(`
      SELECT
        brand.id::text AS id,
        brand.name AS name,
        brand.slug AS slug,
        brand.logotype AS logotype,
        MIN(nomenclature."pricePerMonth")::text AS min_price
      ${VISIBLE_BRANDS_FROM}
      ${filter}
      GROUP BY brand.id, brand.name, brand.slug, brand.logotype
      ORDER BY brand.name ASC, brand.id ASC
      LIMIT $${limitIndex} OFFSET $${offsetIndex}
    `, queryParams);

    const countParams = pattern ? [pattern] : [];
    const count = await this.sourceDataSource.query<Array<{ total: string }>>(`
      SELECT COUNT(DISTINCT brand.id)::text AS total
      ${VISIBLE_BRANDS_FROM}
      ${filter}
    `, countParams);

    return {
      data: await Promise.all(rows.map((row) => this.toListItem(row))),
      pagination: { total: Number(count[0]?.total ?? 0), limit: query.limit, offset: query.offset },
    };
  }

  async findOne(identifier: string): Promise<BrandDetailDto> {
    const rows = await this.sourceDataSource.query<BrandRow[]>(`
      SELECT
        brand.id::text AS id,
        brand.name AS name,
        brand.slug AS slug,
        brand.description AS description,
        brand.logotype AS logotype,
        MIN(nomenclature."pricePerMonth")::text AS min_price
      ${VISIBLE_BRANDS_FROM}
      AND (brand.id::text = $1 OR brand.slug = $1 OR brand.code1c = $1)
      GROUP BY brand.id, brand.name, brand.slug, brand.description, brand.logotype
    `, [identifier]);
    const brand = rows[0];
    if (!brand) {
      throw new NotFoundException({ code: 'BRAND_NOT_FOUND', message: 'Brand not found.' });
    }

    return { ...(await this.toListItem(brand)), description: brand.description ?? null };
  }

  private async toListItem(row: BrandRow): Promise<BrandListItemDto> {
    return {
      id: row.id,
      name: row.name,
      slug: row.slug,
      logoUrl: await this.minioReadService.getReadUrl(row.logotype),
      minPrice: row.min_price,
    };
  }
}
