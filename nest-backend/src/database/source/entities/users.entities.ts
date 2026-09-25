import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ schema: 'public', name: 'custom_user' })
export class CustomUserEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 128, select: false }) password!: string;
  @Column({ name: 'last_login', type: 'timestamptz', nullable: true }) lastLogin!: Date | null;
  @Column({ name: 'is_superuser', type: 'boolean' }) isSuperuser!: boolean;
  @Column({ type: 'varchar', length: 100, nullable: true }) avatar!: string | null;
  @Column({ name: 'last_name', type: 'varchar', length: 150, nullable: true }) lastName!: string | null;
  @Column({ name: 'first_name', type: 'varchar', length: 150, nullable: true }) firstName!: string | null;
  @Column({ name: 'middle_name', type: 'varchar', length: 150, nullable: true }) middleName!: string | null;
  @Column({ type: 'varchar', length: 32 }) role!: string;
  @Column({ name: 'phone_number', type: 'varchar', length: 128, nullable: true }) phoneNumber!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) email!: string | null;
  @Column({ name: 'is_active', type: 'boolean' }) isActive!: boolean;
  @Column({ name: 'is_staff', type: 'boolean' }) isStaff!: boolean;
  @Column({ type: 'timestamptz' }) created!: Date;
  @Column({ name: 'code1c', type: 'varchar', nullable: true }) code1c!: string | null;
  @Column({ name: 'token_1c_access', type: 'text', nullable: true, select: false }) token1cAccess!: string | null;
  @Column({ name: 'token_1c_refresh', type: 'text', nullable: true, select: false }) token1cRefresh!: string | null;
}

@Entity({ schema: 'public', name: 'contact_info' })
export class ContactInfoEntity {
  @PrimaryColumn('uuid') id!: string;
  @Column({ type: 'boolean' }) basic!: boolean;
  @Column({ type: 'varchar', length: 255, nullable: true }) type!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) vidtel!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) vidmail!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) meaning!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) ext!: string | null;
  @Column({ type: 'varchar', length: 255, nullable: true }) comment!: string | null;
  @Column({ name: 'user_id', type: 'uuid' }) userId!: string;
}
