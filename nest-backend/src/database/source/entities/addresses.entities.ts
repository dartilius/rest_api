import { Column, Entity, PrimaryColumn } from 'typeorm';

/** Django address reference data. Foreign keys are represented by their physical UUID columns. */
@Entity({ schema: 'public', name: 'addresses_country' })
export class CountryEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255, unique: true }) name!: string;
}

@Entity({ schema: 'public', name: 'addresses_federal_district' })
export class FederalDistrictEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'country_id', type: 'uuid' }) countryId!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'abbreviated_name', type: 'varchar', length: 50 }) abbreviatedName!: string;
}

@Entity({ schema: 'public', name: 'addresses_type_region' })
export class TypeRegionEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255, unique: true }) name!: string;
  @Column({ name: 'abbreviated_name', type: 'varchar', length: 50 }) abbreviatedName!: string;
  @Column({ name: 'show_before_name', type: 'boolean' }) showBeforeName!: boolean;
  @Column({ name: 'skip_in_name', type: 'boolean' }) skipInName!: boolean;
}

@Entity({ schema: 'public', name: 'addresses_timezone' })
export class TimezoneEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255, unique: true }) name!: string;
  @Column({ name: 'offset_utc', type: 'integer' }) offsetUtc!: number;
  @Column({ name: 'offset_moscow', type: 'integer' }) offsetMoscow!: number;
}

@Entity({ schema: 'public', name: 'addresses_region' })
export class RegionEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'abbreviated_name', type: 'varchar', length: 255, nullable: true }) abbreviatedName!: string | null;
  @Column({ name: 'federal_district_id', type: 'uuid' }) federalDistrictId!: string;
  @Column({ name: 'type_region_id', type: 'uuid' }) typeRegionId!: string;
  @Column({ name: 'timezone_id', type: 'uuid', nullable: true }) timezoneId!: string | null;
}

@Entity({ schema: 'public', name: 'addresses_locality_type' })
export class LocalityTypeEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255, unique: true }) name!: string;
  @Column({ name: 'abbreviated_name', type: 'varchar', length: 50, nullable: true }) abbreviatedName!: string | null;
  @Column({ name: 'show_before_name', type: 'boolean' }) showBeforeName!: boolean;
  @Column({ name: 'has_administrative_territory', type: 'boolean' }) hasAdministrativeTerritory!: boolean;
}

@Entity({ schema: 'public', name: 'addresses_city' })
export class CityEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ type: 'varchar', length: 255 }) slug!: string;
  @Column({ name: 'region_id', type: 'uuid' }) regionId!: string;
  @Column({ name: 'locality_type_id', type: 'uuid' }) localityTypeId!: string;
  @Column({ name: 'timezone_id', type: 'uuid', nullable: true }) timezoneId!: string | null;
  @Column({ name: 'has_atd', type: 'boolean' }) hasAtd!: boolean;
  @Column({ name: 'atd_type', type: 'varchar', length: 255, nullable: true }) atdType!: string | null;
  @Column({ name: 'has_administrative_territory', type: 'boolean' }) hasAdministrativeTerritory!: boolean;
}

@Entity({ schema: 'public', name: 'addresses_administrative_territory' })
export class AdministrativeTerritoryEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'city_id', type: 'uuid' }) cityId!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
}

@Entity({ schema: 'public', name: 'addresses_administrative_territorial_unit' })
export class AdministrativeTerritorialUnitEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'city_id', type: 'uuid' }) cityId!: string;
  @Column({ name: 'administrative_territory_id', type: 'uuid', nullable: true }) administrativeTerritoryId!: string | null;
}

@Entity({ schema: 'public', name: 'addresses_street_type' })
export class StreetTypeEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'abbreviated_name', type: 'varchar', length: 50, nullable: true }) abbreviatedName!: string | null;
  @Column({ name: 'show_before_name', type: 'boolean' }) showBeforeName!: boolean;
}

@Entity({ schema: 'public', name: 'addresses_street' })
export class StreetEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'city_id', type: 'uuid' }) cityId!: string;
  @Column({ name: 'street_type_id', type: 'uuid', nullable: true }) streetTypeId!: string | null;
  @Column({ type: 'varchar', length: 255 }) name!: string;
}

@Entity({ schema: 'public', name: 'addresses_house' })
export class HouseEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'street_id', type: 'uuid' }) streetId!: string;
  @Column({ type: 'varchar', length: 31 }) number!: string;
}

@Entity({ schema: 'public', name: 'addresses_building' })
export class BuildingEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'house_id', type: 'uuid' }) houseId!: string;
  @Column({ type: 'varchar', length: 31 }) number!: string;
}

@Entity({ schema: 'public', name: 'addresses_coordinates' })
export class CoordinatesEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 31, nullable: true }) latitude!: string | null;
  @Column({ type: 'varchar', length: 31, nullable: true }) longitude!: string | null;
}

@Entity({ schema: 'public', name: 'addresses_address' })
export class AddressEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'country_id', type: 'uuid', nullable: true }) countryId!: string | null;
  @Column({ name: 'federal_district_id', type: 'uuid', nullable: true }) federalDistrictId!: string | null;
  @Column({ name: 'region_id', type: 'uuid', nullable: true }) regionId!: string | null;
  @Column({ name: 'city_id', type: 'uuid', nullable: true }) cityId!: string | null;
  @Column({ name: 'administrative_territory_id', type: 'uuid', nullable: true }) administrativeTerritoryId!: string | null;
  @Column({ name: 'administrative_unit_id', type: 'uuid', nullable: true }) administrativeUnitId!: string | null;
  @Column({ name: 'street_id', type: 'uuid', nullable: true }) streetId!: string | null;
  @Column({ name: 'house_id', type: 'uuid', nullable: true }) houseId!: string | null;
  @Column({ name: 'building_id', type: 'uuid', nullable: true }) buildingId!: string | null;
  @Column({ name: 'coordinates_id', type: 'uuid', nullable: true }) coordinatesId!: string | null;
  @Column({ type: 'varchar', length: 100, nullable: true }) microdistrict!: string | null;
  @Column({ name: 'index', type: 'varchar', length: 6, nullable: true }) postalIndex!: string | null;
  @Column({ type: 'varchar', length: 20, nullable: true }) latitude!: string | null;
  @Column({ type: 'varchar', length: 20, nullable: true }) longitude!: string | null;
}
