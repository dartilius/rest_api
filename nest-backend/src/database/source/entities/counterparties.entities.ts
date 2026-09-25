import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ schema: 'public', name: 'counterparty_categories' })
export class CounterpartyCategoryEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 64 }) name!: string;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
}

@Entity({ schema: 'public', name: 'counterparties' })
export class CounterpartyEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'owner_id', type: 'uuid', nullable: true }) ownerId!: string | null;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'code1c', type: 'varchar', length: 64, nullable: true }) code1c!: string | null;
  @Column({ type: 'varchar', length: 64, nullable: true }) opf!: string | null;
  @Column({ type: 'varchar', length: 64, nullable: true }) inn!: string | null;
  @Column({ name: 'first_name', type: 'varchar', length: 64 }) firstName!: string;
  @Column({ name: 'middle_name', type: 'varchar', length: 64 }) middleName!: string;
  @Column({ name: 'last_name', type: 'varchar', length: 64 }) lastName!: string;
  @Column({ type: 'varchar', length: 256, nullable: true }) description!: string | null;
  @Column({ type: 'varchar', length: 256, nullable: true }) keyword!: string | null;
  @Column({ name: 'additional_name', type: 'varchar', length: 64, nullable: true }) additionalName!: string | null;
  @Column({ type: 'boolean' }) broadcast!: boolean;
  @Column({ name: 'address_id', type: 'uuid', nullable: true }) addressId!: string | null;
}

@Entity({ schema: 'public', name: 'counterparty_contact_info' })
export class CounterpartyContactInfoEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'boolean' }) basic!: boolean;
  @Column({ type: 'varchar', length: 255, nullable: true }) type!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) vidtel!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) vidmail!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) meaning!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) ext!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) comment!: string | null;
  @Column({ name: 'counterparty_id', type: 'uuid' }) counterpartyId!: string;
}

@Entity({ schema: 'public', name: 'counterparty_category_assignments' })
export class CounterpartyCategoryAssignmentEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'counterparty_id', type: 'uuid' }) counterpartyId!: string;
  @Column({ name: 'category_id', type: 'uuid' }) categoryId!: string;
  @Column({ name: 'assigned_at', type: 'timestamptz' }) assignedAt!: Date;
}

/** Auto-created Django M2M table: Counterparty.contact_persons. */
@Entity({ schema: 'public', name: 'counterparties_contact_persons' })
export class CounterpartyContactPersonEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'counterparty_id', type: 'uuid' }) counterpartyId!: string;
  @Column({ name: 'customuser_id', type: 'uuid' }) customUserId!: string;
}

/** Auto-created Django M2M table: Counterparty.brands. */
@Entity({ schema: 'public', name: 'counterparties_brands' })
export class CounterpartyBrandEntity {
  @PrimaryColumn({ type: 'bigint' }) id!: string;
  @Column({ name: 'counterparty_id', type: 'uuid' }) counterpartyId!: string;
  @Column({ name: 'brand_id', type: 'uuid' }) brandId!: string;
}
