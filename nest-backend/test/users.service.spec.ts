import assert from 'node:assert/strict';
import test from 'node:test';
import type { DataSource } from 'typeorm';
import { UsersService } from '../src/users/users.service';

test('returns a current user profile without password or 1C tokens', async () => {
  const source = { query: async () => [{ id: 'u', email: 'person@example.test', phone_number: '+79990000000', first_name: 'Ivan', last_name: 'Ivanov', middle_name: null, role: 'ordinary', avatar: null, created: '2026-01-01', code1c: 'USER-1' }] } as unknown as DataSource;
  const service = new UsersService(source);

  const result = await service.me({ id: 'u', role: 'ordinary', tokenVersion: 'rs256' });

  assert.deepEqual(result, { id: 'u', email: 'person@example.test', phoneNumber: '+79990000000', fullName: { firstName: 'Ivan', lastName: 'Ivanov', middleName: null }, role: 'ordinary', avatar: null, created: '2026-01-01', code1c: 'USER-1' });
  assert.equal('password' in result, false);
});
