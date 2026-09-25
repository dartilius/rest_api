import { Column, Entity, PrimaryColumn } from 'typeorm';

type JsonObject = Record<string, unknown>;

@Entity({ schema: 'public', name: 'type_of_place' })
export class TypeOfPlaceEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ type: 'varchar', nullable: true }) tariff!: string | null;
  @Column({ name: 'tariff_single', type: 'varchar', nullable: true }) tariffSingle!: string | null;
  @Column({ type: 'varchar', length: 50, nullable: true }) abbreviation!: string | null;
  @Column({ name: 'code1c', type: 'varchar', length: 64, nullable: true }) code1c!: string | null;
  @Column({ name: 'is_mall', type: 'boolean' }) isMall!: boolean;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
}

@Entity({ schema: 'public', name: 'nomenclature' })
export class NomenclatureEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'owner_id', type: 'uuid', nullable: true }) ownerId!: string | null;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'for_web', type: 'boolean' }) forWeb!: boolean;
  @Column({ type: 'boolean' }) broadcast!: boolean;
  @Column({ name: 'slots_per_hour', type: 'varchar', nullable: true }) slotsPerHour!: string | null;
  @Column({ name: 'external_video_media', type: 'varchar', nullable: true }) externalVideoMedia!: string | null;
  @Column({ name: 'external_audio_media', type: 'varchar', nullable: true }) externalAudioMedia!: string | null;
  @Column({ name: 'internal_video_media', type: 'varchar', nullable: true }) internalVideoMedia!: string | null;
  @Column({ name: 'internal_audio_media', type: 'varchar', nullable: true }) internalAudioMedia!: string | null;
  @Column({ name: 'worktime_start', type: 'time', nullable: true }) worktimeStart!: string | null;
  @Column({ name: 'worktime_end', type: 'time', nullable: true }) worktimeEnd!: string | null;
  @Column({ name: 'id_rasb', type: 'varchar', nullable: true }) idRasb!: string | null;
  @Column({ type: 'varchar', nullable: true }) square!: string | null;
  @Column({ type: 'varchar', nullable: true }) possibility!: string | null;
  /** Custom Django Article field; verified against PostgreSQL before enabling production reads. */
  @Column({ type: 'integer' }) article!: number;
  @Column({ type: 'text', nullable: true }) description!: string | null;
  @Column({ name: 'responsible_radio_id', type: 'uuid', nullable: true }) responsibleRadioId!: string | null;
  @Column({ name: 'responsible_ad_id', type: 'uuid', nullable: true }) responsibleAdId!: string | null;
  @Column({ name: 'responsible_technic_id', type: 'uuid', nullable: true }) responsibleTechnicId!: string | null;
  @Column({ name: 'responsible_technic_on_address_id', type: 'uuid', nullable: true }) responsibleTechnicOnAddressId!: string | null;
  @Column({ name: 'responsible_placement_marketing_id', type: 'uuid', nullable: true }) responsiblePlacementMarketingId!: string | null;
  @Column({ type: 'varchar', length: 31 }) timezone!: string;
  @Column({ name: 'code1c', type: 'varchar', length: 64, nullable: true }) code1c!: string | null;
  @Column({ type: 'varchar', length: 127 }) version!: string;
  @Column({ type: 'jsonb' }) settings!: JsonObject;
  @Column({ name: 'applied_settings_revision', type: 'integer', nullable: true }) appliedSettingsRevision!: number | null;
  @Column({ name: 'station_capabilities', type: 'jsonb', nullable: true }) stationCapabilities!: JsonObject | null;
  @Column({ name: 'visual_output_settings', type: 'jsonb', nullable: true }) visualOutputSettings!: JsonObject | null;
  @Column({ name: 'hw_info', type: 'jsonb', nullable: true }) hwInfo!: JsonObject | null;
  @Column({ name: 'runtime_state', type: 'jsonb', nullable: true }) runtimeState!: JsonObject | null;
  @Column({ name: 'brand_id', type: 'uuid', nullable: true }) brandId!: string | null;
  @Column({ name: 'legalEntity_id', type: 'uuid', nullable: true }) legalEntityId!: string | null;
  @Column({ name: 'contentType', type: 'varchar', length: 255 }) contentType!: string;
  @Column({ name: 'typeOfPlace_id', type: 'uuid', nullable: true }) typeOfPlaceId!: string | null;
  @Column({ name: 'pricePerMonth', type: 'numeric', precision: 10, scale: 2 }) pricePerMonth!: string;
  @Column({ name: 'old_catalog_slug', type: 'varchar', length: 512 }) oldCatalogSlug!: string;
  @Column({ name: 'search_vector', type: 'text' }) searchVector!: string;
}

@Entity({ schema: 'public', name: 'nomenclature_tenant' })
export class NomenclatureTenantEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ name: 'tenant_id', type: 'uuid' }) tenantId!: string;
  @Column({ type: 'varchar', length: 10 }) floor!: string;
  @Column({ type: 'boolean' }) atm!: boolean;
  @Column({ name: 'brand_id', type: 'uuid', nullable: true }) brandId!: string | null;
}

@Entity({ schema: 'public', name: 'discount_rule' })
export class DiscountRuleEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ name: 'days_from', type: 'integer' }) daysFrom!: number;
  @Column({ name: 'days_to', type: 'integer', nullable: true }) daysTo!: number | null;
  @Column({ type: 'numeric' }) coefficient!: string;
}

@Entity({ schema: 'public', name: 'statistic_receipt' })
export class StatisticReceiptEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ name: 'event_id', type: 'uuid' }) eventId!: string;
  @Column({ name: 'stat_type', type: 'varchar', length: 16 }) statType!: string;
  @Column({ name: 'received_at', type: 'timestamptz' }) receivedAt!: Date;
}

@Entity({ schema: 'public', name: 'nomenclatures_stationcredential' })
export class StationCredentialEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid', unique: true }) nomenclatureId!: string;
  @Column({ name: 'token_hash', type: 'varchar', length: 64, unique: true, select: false }) tokenHash!: string;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @Column({ name: 'rotated_at', type: 'timestamptz' }) rotatedAt!: Date;
}

@Entity({ schema: 'public', name: 'nomenclatures_stationinstallation' })
export class StationInstallationEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ name: 'created_by_id', type: 'uuid' }) createdById!: string;
  @Column({ name: 'token_hash', type: 'varchar', length: 64, unique: true, select: false }) tokenHash!: string;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @Column({ name: 'rotated_at', type: 'timestamptz' }) rotatedAt!: Date;
}

@Entity({ schema: 'public', name: 'nomenclatures_stationcommandv2' })
export class StationCommandV2Entity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'command_id', type: 'uuid', unique: true }) commandId!: string;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ type: 'varchar', length: 64 }) kind!: string;
  @Column({ type: 'jsonb' }) body!: JsonObject;
  @Column({ type: 'varchar', length: 16 }) status!: string;
  @Column({ type: 'jsonb', nullable: true }) result!: JsonObject | null;
  @Column({ name: 'expires_at', type: 'timestamptz', nullable: true }) expiresAt!: Date | null;
  @Column({ name: 'delivered_at', type: 'timestamptz', nullable: true }) deliveredAt!: Date | null;
  @Column({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @Column({ name: 'updated_at', type: 'timestamptz' }) updatedAt!: Date;
}

@Entity({ schema: 'public', name: 'availability' })
export class NomenclatureAvailabilityEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'last_answer_date', type: 'timestamptz' }) lastAnswerDate!: Date;
  @Column({ name: 'client_id', type: 'uuid', unique: true }) clientId!: string;
  @Column({ type: 'smallint' }) status!: number;
}

@Entity({ schema: 'public', name: 'nomenclature_addresses' })
export class NomenclatureAddressEntity {
  @PrimaryColumn({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ name: 'address_id', type: 'uuid', nullable: true }) addressId!: string | null;
}

@Entity({ schema: 'public', name: 'status_history' })
export class StatusHistoryEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'client_id', type: 'uuid' }) clientId!: string;
  @Column({ name: 'change_time', type: 'timestamptz' }) changeTime!: Date;
  @Column({ type: 'smallint' }) status!: number;
}

@Entity({ schema: 'public', name: 'nomenclature_images' })
export class NomenclatureImageEntity {
  @PrimaryColumn('uuid') id!: string;
  /** Object key in existing MinIO; Nest only reads through a dedicated key. */
  @Column({ type: 'varchar', length: 100 }) source!: string;
  @Column({ type: 'varchar', length: 31 }) type!: string;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ type: 'varchar', length: 64 }) hash!: string;
}

@Entity({ schema: 'public', name: 'nomenclature_videos' })
export class NomenclatureVideoEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 100 }) source!: string;
  @Column({ type: 'varchar', length: 31 }) type!: string;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'nomenclature_id', type: 'uuid' }) nomenclatureId!: string;
  @Column({ type: 'varchar', length: 64 }) hash!: string;
}
