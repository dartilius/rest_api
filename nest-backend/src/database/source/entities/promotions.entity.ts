import { Column, Entity, PrimaryColumn } from 'typeorm';

/** Django-owned promotion. Registered on the read-only source connection only. */
@Entity({ schema: 'public', name: 'promotions' })
export class PromotionEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ name: 'owner_id', type: 'uuid', nullable: true }) ownerId!: string | null;
  @Column({ type: 'varchar', length: 255 }) name!: string;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'start_period', type: 'date', nullable: true }) startPeriod!: string | null;
  @Column({ name: 'end_period', type: 'date', nullable: true }) endPeriod!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) description!: string | null;
  @Column({ name: 'code1c', type: 'varchar', length: 255, nullable: true }) code1c!: string | null;
  @Column({ name: 'counterparty_id', type: 'uuid', nullable: true }) counterpartyId!: string | null;
}
