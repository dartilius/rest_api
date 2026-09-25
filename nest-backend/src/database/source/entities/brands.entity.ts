import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ schema: 'public', name: 'brands' })
export class BrandEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 100, unique: true, nullable: true }) slug!: string | null;
  @Column({ name: 'code1c', type: 'varchar', length: 64, unique: true, nullable: true }) code1c!: string | null;
  @Column({ type: 'varchar', length: 64 }) name!: string;
  @Column({ type: 'text', nullable: true }) description!: string | null;
  /** Object key in the existing local-media MinIO bucket. Nest does not write it. */
  @Column({ type: 'varchar', length: 100, nullable: true }) logotype!: string | null;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'is_deleted', type: 'boolean' }) isDeleted!: boolean;
  @Column({ name: 'deleted_at', type: 'timestamptz', nullable: true }) deletedAt!: Date | null;
}
