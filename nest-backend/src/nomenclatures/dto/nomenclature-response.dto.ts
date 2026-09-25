import { ApiProperty } from '@nestjs/swagger';

export class NomenclatureImageDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty({ nullable: true, format: 'uri' }) url!: string | null;
}

export class NomenclatureBrandDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty() name!: string;
  @ApiProperty({ nullable: true, format: 'uri' }) logoUrl!: string | null;
}

export class NomenclatureTypeOfPlaceDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty() name!: string;
  @ApiProperty({ nullable: true }) abbreviation!: string | null;
}

export class NomenclatureCoordinatesDto {
  @ApiProperty({ nullable: true }) latitude!: string | null;
  @ApiProperty({ nullable: true }) longitude!: string | null;
}

export class NomenclatureAddressDto {
  @ApiProperty() name!: string;
  @ApiProperty({ type: NomenclatureCoordinatesDto }) coordinates!: NomenclatureCoordinatesDto;
}

export class NomenclatureDetailAddressDto extends NomenclatureAddressDto {
  @ApiProperty({ description: 'Full human-readable address.' }) fullAddress!: string;
}

export class NomenclatureListItemDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty({ type: NomenclatureBrandDto, nullable: true }) brand!: NomenclatureBrandDto | null;
  @ApiProperty({ type: NomenclatureImageDto, nullable: true }) exterior!: NomenclatureImageDto | null;
  @ApiProperty({ type: NomenclatureAddressDto }) address!: NomenclatureAddressDto;
  @ApiProperty({ type: NomenclatureTypeOfPlaceDto, nullable: true }) typeOfPlace!: NomenclatureTypeOfPlaceDto | null;
  @ApiProperty({ description: 'Decimal string in the source currency.' }) pricePerMonth!: string;
  @ApiProperty({ nullable: true }) slotsPerHour!: string | null;
  @ApiProperty() oldCatalogSlug!: string;
}

export class NomenclatureDetailDto extends NomenclatureListItemDto {
  @ApiProperty({ type: NomenclatureDetailAddressDto }) declare address: NomenclatureDetailAddressDto;
  @ApiProperty({ nullable: true }) description!: string | null;
  @ApiProperty() contentType!: string;
  @ApiProperty({ nullable: true, example: '09:00' }) worktimeStart!: string | null;
  @ApiProperty({ nullable: true, example: '22:00' }) worktimeEnd!: string | null;
  @ApiProperty({ nullable: true }) possibility!: string | null;
  @ApiProperty({ type: NomenclatureImageDto, isArray: true }) interior!: NomenclatureImageDto[];
}

export class NomenclaturesListResponseDto {
  @ApiProperty({ type: NomenclatureListItemDto, isArray: true }) data!: NomenclatureListItemDto[];
  @ApiProperty({ example: { total: 1, limit: 24, offset: 0 } }) pagination!: { total: number; limit: number; offset: number };
}

export class NomenclatureIdFacetDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty() name!: string;
  @ApiProperty() count!: number;
}

export class NomenclatureCityFacetDto {
  @ApiProperty() slug!: string;
  @ApiProperty() name!: string;
  @ApiProperty() count!: number;
}

export class NomenclatureValueFacetDto {
  @ApiProperty() value!: string;
  @ApiProperty() count!: number;
}

export class NomenclatureBooleanFacetDto {
  @ApiProperty() value!: boolean;
  @ApiProperty() count!: number;
}

export class NomenclaturePriceFacetDto {
  @ApiProperty({ nullable: true, description: 'Decimal string.' }) min!: string | null;
  @ApiProperty({ nullable: true, description: 'Decimal string.' }) max!: string | null;
}

export class NomenclatureFilterOptionsDto {
  @ApiProperty({ type: NomenclatureIdFacetDto, isArray: true }) brands!: NomenclatureIdFacetDto[];
  @ApiProperty({ type: NomenclatureIdFacetDto, isArray: true }) typesOfPlace!: NomenclatureIdFacetDto[];
  @ApiProperty({ type: NomenclatureCityFacetDto, isArray: true }) cities!: NomenclatureCityFacetDto[];
  @ApiProperty({ type: NomenclatureValueFacetDto, isArray: true }) contentTypes!: NomenclatureValueFacetDto[];
  @ApiProperty({ type: NomenclatureValueFacetDto, isArray: true }) versions!: NomenclatureValueFacetDto[];
  @ApiProperty({ type: NomenclatureValueFacetDto, isArray: true }) timezones!: NomenclatureValueFacetDto[];
  @ApiProperty({ type: NomenclatureValueFacetDto, isArray: true }) statuses!: NomenclatureValueFacetDto[];
  @ApiProperty({ type: NomenclatureBooleanFacetDto, isArray: true }) hasFacade!: NomenclatureBooleanFacetDto[];
  @ApiProperty({ type: NomenclaturePriceFacetDto }) price!: NomenclaturePriceFacetDto;
}

export class NomenclatureMapPointDto {
  @ApiProperty({ format: 'uuid' }) id!: string;
  @ApiProperty() name!: string;
  @ApiProperty({ type: NomenclatureCoordinatesDto, nullable: true }) coordinates!: NomenclatureCoordinatesDto | null;
  @ApiProperty({ type: NomenclatureTypeOfPlaceDto, nullable: true }) typeOfPlace!: NomenclatureTypeOfPlaceDto | null;
  @ApiProperty({ type: NomenclatureBrandDto, nullable: true }) brand!: NomenclatureBrandDto | null;
  @ApiProperty({ type: NomenclatureImageDto, nullable: true }) facade!: NomenclatureImageDto | null;
  @ApiProperty({ nullable: true }) perDay!: number | null;
  @ApiProperty({ nullable: true }) perHour!: string | null;
  @ApiProperty() oldCatalogSlug!: string;
}

export class NomenclatureMapResponseDto {
  @ApiProperty() count!: number;
  @ApiProperty({ type: NomenclatureMapPointDto, isArray: true }) results!: NomenclatureMapPointDto[];
}
