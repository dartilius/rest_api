import { ForbiddenException } from '@nestjs/common';
import type { AuthenticatedSiteUser } from '../../auth/django-jwt-verifier.service';

const employeeRoles = new Set(['admin', 'manager', 'superuser', 'administrator']);
const contactPersonRoles = new Set(['ad', 'broadcast']);

export function isEmployee(user: AuthenticatedSiteUser): boolean {
  return user.role !== undefined && employeeRoles.has(user.role);
}

export function isContactPerson(user: AuthenticatedSiteUser): boolean {
  return user.role !== undefined && contactPersonRoles.has(user.role);
}

export function requireEmployee(user: AuthenticatedSiteUser): void {
  if (!isEmployee(user)) {
    throw new ForbiddenException({ code: 'EMPLOYEE_ACCESS_REQUIRED', message: 'Employee access required.' });
  }
}
