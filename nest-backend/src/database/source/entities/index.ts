import { AddressEntity, AdministrativeTerritorialUnitEntity, AdministrativeTerritoryEntity, BuildingEntity, CityEntity, CoordinatesEntity, CountryEntity, FederalDistrictEntity, HouseEntity, LocalityTypeEntity, RegionEntity, StreetEntity, StreetTypeEntity, TimezoneEntity, TypeRegionEntity } from './addresses.entities';
import { BrandEntity } from './brands.entity';
import { CounterpartyBrandEntity, CounterpartyCategoryAssignmentEntity, CounterpartyCategoryEntity, CounterpartyContactInfoEntity, CounterpartyContactPersonEntity, CounterpartyEntity } from './counterparties.entities';
import { DiscountRuleEntity, NomenclatureAddressEntity, NomenclatureAvailabilityEntity, NomenclatureEntity, NomenclatureImageEntity, NomenclatureTenantEntity, NomenclatureVideoEntity, StatisticReceiptEntity, StationCommandV2Entity, StationCredentialEntity, StationInstallationEntity, StatusHistoryEntity, TypeOfPlaceEntity } from './nomenclatures.entities';
import { ContactInfoEntity, CustomUserEntity } from './users.entities';

/**
 * Entities owned by Django. They are intentionally registered on a separate,
 * read-only connection; no migration or synchronize operation is ever run here.
 */
export const sourceEntities = [
  CountryEntity, FederalDistrictEntity, TypeRegionEntity, TimezoneEntity, RegionEntity,
  LocalityTypeEntity, CityEntity, AdministrativeTerritoryEntity,
  AdministrativeTerritorialUnitEntity, StreetTypeEntity, StreetEntity, HouseEntity,
  BuildingEntity, CoordinatesEntity, AddressEntity,
  BrandEntity,
  CustomUserEntity, ContactInfoEntity,
  CounterpartyCategoryEntity, CounterpartyEntity, CounterpartyContactInfoEntity,
  CounterpartyCategoryAssignmentEntity, CounterpartyContactPersonEntity, CounterpartyBrandEntity,
  TypeOfPlaceEntity, NomenclatureEntity, NomenclatureTenantEntity, DiscountRuleEntity,
  StatisticReceiptEntity, StationCredentialEntity, StationInstallationEntity,
  StationCommandV2Entity, NomenclatureAvailabilityEntity, NomenclatureAddressEntity,
  StatusHistoryEntity, NomenclatureImageEntity, NomenclatureVideoEntity,
];

export {
  AddressEntity, AdministrativeTerritorialUnitEntity, AdministrativeTerritoryEntity,
  BrandEntity, BuildingEntity, CityEntity, ContactInfoEntity, CoordinatesEntity,
  CounterpartyBrandEntity, CounterpartyCategoryAssignmentEntity, CounterpartyCategoryEntity,
  CounterpartyContactInfoEntity, CounterpartyContactPersonEntity, CounterpartyEntity,
  CountryEntity, CustomUserEntity, DiscountRuleEntity, FederalDistrictEntity, HouseEntity,
  LocalityTypeEntity, NomenclatureAddressEntity, NomenclatureAvailabilityEntity,
  NomenclatureEntity, NomenclatureImageEntity, NomenclatureTenantEntity, NomenclatureVideoEntity,
  RegionEntity, StatisticReceiptEntity, StationCommandV2Entity, StationCredentialEntity,
  StationInstallationEntity, StatusHistoryEntity, StreetEntity, StreetTypeEntity, TimezoneEntity,
  TypeOfPlaceEntity, TypeRegionEntity,
};
