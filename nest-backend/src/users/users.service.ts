import { Injectable, NotFoundException } from '@nestjs/common'
import { InjectDataSource } from '@nestjs/typeorm'
import { DataSource } from 'typeorm'
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service'
import { requireEmployee } from '../common/auth/site-access'
import { SOURCE_DATABASE_CONNECTION } from '../database/source/source-data-source.options'
import { UserQueryDto } from './dto/user-query.dto'

type UserRow = {
	id: string
	email: string | null
	phone_number: string | null
	first_name: string | null
	last_name: string | null
	middle_name: string | null
	role: string
	avatar: string | null
	created: string
	code1c: string | null
}
export type UserResponse = {
	id: string
	email: string | null
	phoneNumber: string | null
	fullName: { firstName: string | null; lastName: string | null; middleName: string | null }
	role: string
	avatar: string | null
	created: string
	code1c: string | null
}
export type UsersListResponse = {
	data: UserResponse[]
	pagination: { total: number; limit: number; offset: number }
}

function toResponse(row: UserRow): UserResponse {
	return {
		id: row.id,
		email: row.email,
		phoneNumber: row.phone_number,
		fullName: { firstName: row.first_name, lastName: row.last_name, middleName: row.middle_name },
		role: row.role,
		avatar: row.avatar,
		created: row.created,
		code1c: row.code1c,
	}
}
function like(value: string): string {
	return `%${value.replaceAll('!', '!!').replaceAll('%', '!%').replaceAll('_', '!_')}%`
}

@Injectable()
export class UsersService {
	constructor(@InjectDataSource(SOURCE_DATABASE_CONNECTION) private readonly source: DataSource) {}

	async me(user: AuthenticatedSiteUser): Promise<UserResponse> {
		return this.findActive(user.id)
	}

	async list(actor: AuthenticatedSiteUser, query: UserQueryDto): Promise<UsersListResponse> {
		requireEmployee(actor)
		const params: unknown[] = []
		const filters = ['site_user.is_active = TRUE']
		if (query.search?.trim()) {
			params.push(like(query.search.trim()))
			filters.push(
				`(site_user.first_name ILIKE $${params.length} ESCAPE '!' OR site_user.last_name ILIKE $${params.length} ESCAPE '!' OR site_user.middle_name ILIKE $${params.length} ESCAPE '!' OR site_user.email ILIKE $${params.length} ESCAPE '!')`,
			)
		}
		if (query.role?.trim()) {
			params.push(query.role.trim())
			filters.push(`site_user.role = $${params.length}`)
		}
		const where = `WHERE ${filters.join(' AND ')}`
		const limitIndex = params.push(query.limit)
		const offsetIndex = params.push(query.offset)
		const countParams = params.slice(0, -2)
		const [rows, count] = await Promise.all([
			this.source.query<UserRow[]>(
				`${this.select()} FROM public.custom_user site_user ${where} ORDER BY site_user.created DESC, site_user.id DESC LIMIT $${limitIndex} OFFSET $${offsetIndex}`,
				params,
			),
			this.source.query<Array<{ total: string }>>(
				`SELECT COUNT(*)::text AS total FROM public.custom_user site_user ${where}`,
				countParams,
			),
		])
		return {
			data: rows.map(toResponse),
			pagination: { total: Number(count[0]?.total ?? 0), limit: query.limit, offset: query.offset },
		}
	}

	async findOne(actor: AuthenticatedSiteUser, identifier: string): Promise<UserResponse> {
		requireEmployee(actor)
		const rows = await this.source.query<UserRow[]>(
			`${this.select()} FROM public.custom_user site_user WHERE site_user.is_active = TRUE AND (site_user.id::text = $1 OR site_user.code1c = $1) ORDER BY site_user.created DESC, site_user.id DESC LIMIT 1`,
			[identifier],
		)
		const user = rows[0]
		if (!user) throw new NotFoundException({ code: 'USER_NOT_FOUND', message: 'User not found.' })
		return toResponse(user)
	}

	private async findActive(id: string): Promise<UserResponse> {
		const rows = await this.source.query<UserRow[]>(
			`${this.select()} FROM public.custom_user site_user WHERE site_user.id::text = $1 AND site_user.is_active = TRUE`,
			[id],
		)
		const user = rows[0]
		if (!user) throw new NotFoundException({ code: 'USER_NOT_FOUND', message: 'User not found.' })
		return toResponse(user)
	}

	private select(): string {
		return 'SELECT site_user.id::text AS id, site_user.email, site_user.phone_number, site_user.first_name, site_user.last_name, site_user.middle_name, site_user.role, site_user.avatar, site_user.created::text AS created, site_user.code1c'
	}
}
